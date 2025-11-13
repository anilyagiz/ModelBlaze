# 🌐 ModelBlaze Web Architecture (Supabase + Next.js)

## 🏗️ Tech Stack

```
Frontend:  Next.js 14 + React + TailwindCSS
Backend:   Supabase (PostgreSQL + Auth + Storage)
Jobs:      GitHub Actions or Modal
Payments:  Stripe
Hosting:   Vercel (FREE)
```

**Total Cost: $25-50/month**

---

## 📁 Project Structure

```
modelblaze-web/
├── app/                        # Next.js 14 app directory
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/
│   │   ├── dashboard/
│   │   ├── optimize/
│   │   ├── history/
│   │   └── settings/
│   ├── api/
│   │   ├── optimize/
│   │   ├── stripe/
│   │   └── webhooks/
│   └── page.tsx              # Landing page
│
├── components/
│   ├── ui/                   # Shadcn UI components
│   ├── ModelUploader.tsx
│   ├── OptimizationProgress.tsx
│   ├── ResultsChart.tsx
│   └── PricingCards.tsx
│
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── database.types.ts
│   ├── stripe/
│   │   └── client.ts
│   └── optimizer/            # Python code integration
│       └── runner.ts
│
├── public/
│   └── examples/
│
└── python/                   # Existing ModelBlaze code
    └── src/                  # Copy from main repo
```

---

## 🔐 Supabase Setup (5 minutes)

### 1. Create Project
```bash
# Go to supabase.com
# Create new project
# Copy: Project URL, anon key, service_role key
```

### 2. Database Schema
```sql
-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Profiles (extends auth.users)
create table profiles (
  id uuid references auth.users primary key,
  email text,
  full_name text,
  avatar_url text,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Subscriptions
create table subscriptions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users not null,
  plan text not null check (plan in ('free', 'pro', 'business', 'enterprise')),
  stripe_customer_id text unique,
  stripe_subscription_id text unique,
  status text not null check (status in ('active', 'canceled', 'past_due', 'trialing')),
  current_period_start timestamp,
  current_period_end timestamp,
  cancel_at_period_end boolean default false,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Optimizations
create table optimizations (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users not null,

  -- Input
  original_filename text not null,
  original_model_path text not null,
  target_device text not null,
  optimization_level text not null,
  quantization_mode text,
  pruning_sparsity float,

  -- Output
  optimized_model_path text,

  -- Status
  status text not null check (status in ('pending', 'processing', 'completed', 'failed')),
  error_message text,

  -- Metrics
  original_size_mb float,
  optimized_size_mb float,
  size_reduction_pct float,
  latency_original_ms float,
  latency_optimized_ms float,
  latency_speedup float,
  memory_reduction_pct float,

  -- Report
  report_html text,
  report_json jsonb,

  -- Timestamps
  created_at timestamp default now(),
  started_at timestamp,
  completed_at timestamp,

  -- Index for queries
  constraint fk_user foreign key (user_id) references auth.users(id) on delete cascade
);

create index idx_optimizations_user_id on optimizations(user_id);
create index idx_optimizations_created_at on optimizations(created_at desc);

-- Usage tracking
create table usage (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users not null,
  month text not null, -- 'YYYY-MM'
  optimizations_count int default 0,
  total_mb_processed float default 0,
  created_at timestamp default now(),
  updated_at timestamp default now(),

  unique(user_id, month)
);

-- Row Level Security (RLS)
alter table profiles enable row level security;
alter table subscriptions enable row level security;
alter table optimizations enable row level security;
alter table usage enable row level security;

-- Profiles policies
create policy "Users can view own profile"
  on profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on profiles for update
  using (auth.uid() = id);

-- Subscriptions policies
create policy "Users can view own subscription"
  on subscriptions for select
  using (auth.uid() = user_id);

-- Optimizations policies
create policy "Users can view own optimizations"
  on optimizations for select
  using (auth.uid() = user_id);

create policy "Users can insert own optimizations"
  on optimizations for insert
  with check (auth.uid() = user_id);

-- Usage policies
create policy "Users can view own usage"
  on usage for select
  using (auth.uid() = user_id);

-- Functions
create or replace function increment_usage(p_user_id uuid, p_month text, p_mb float)
returns void as $$
begin
  insert into usage (user_id, month, optimizations_count, total_mb_processed)
  values (p_user_id, p_month, 1, p_mb)
  on conflict (user_id, month)
  do update set
    optimizations_count = usage.optimizations_count + 1,
    total_mb_processed = usage.total_mb_processed + p_mb,
    updated_at = now();
end;
$$ language plpgsql security definer;

-- Function to check usage limits
create or replace function check_usage_limit(p_user_id uuid)
returns boolean as $$
declare
  v_plan text;
  v_count int;
  v_limit int;
begin
  -- Get user's plan
  select plan into v_plan
  from subscriptions
  where user_id = p_user_id and status = 'active'
  limit 1;

  -- Default to free if no subscription
  v_plan := coalesce(v_plan, 'free');

  -- Get current month's usage
  select coalesce(optimizations_count, 0) into v_count
  from usage
  where user_id = p_user_id
    and month = to_char(now(), 'YYYY-MM');

  -- Set limits based on plan
  case v_plan
    when 'free' then v_limit := 0; -- CLI only
    when 'pro' then v_limit := 10;
    when 'business' then v_limit := 50;
    when 'enterprise' then v_limit := 999999;
    else v_limit := 0;
  end case;

  return v_count < v_limit;
end;
$$ language plpgsql security definer;
```

### 3. Storage Buckets
```sql
-- Create buckets for model storage
insert into storage.buckets (id, name, public)
values
  ('models-original', 'models-original', false),
  ('models-optimized', 'models-optimized', false);

-- Storage policies
create policy "Users can upload own models"
  on storage.objects for insert
  with check (
    bucket_id = 'models-original'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "Users can download own models"
  on storage.objects for select
  using (
    (bucket_id = 'models-original' or bucket_id = 'models-optimized')
    and auth.uid()::text = (storage.foldername(name))[1]
  );
```

---

## 🎨 Next.js Implementation

### Environment Variables (.env.local)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optimization
OPTIMIZATION_WEBHOOK_URL=https://your-api.com/optimize
```

### Supabase Client (lib/supabase/client.ts)
```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

### Model Upload Component (components/ModelUploader.tsx)
```typescript
'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'

export default function ModelUploader({ userId }: { userId: string }) {
  const [uploading, setUploading] = useState(false)
  const [file, setFile] = useState<File | null>(null)

  const supabase = createClient()

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)

    try {
      // Upload to Supabase Storage
      const filePath = `${userId}/${Date.now()}_${file.name}`

      const { error: uploadError } = await supabase.storage
        .from('models-original')
        .upload(filePath, file)

      if (uploadError) throw uploadError

      // Create optimization record
      const { data, error } = await supabase
        .from('optimizations')
        .insert({
          user_id: userId,
          original_filename: file.name,
          original_model_path: filePath,
          target_device: 'mobile',
          optimization_level: 'high',
          status: 'pending',
          original_size_mb: file.size / (1024 * 1024)
        })
        .select()
        .single()

      if (error) throw error

      // Trigger optimization job (webhook to GitHub Actions or Modal)
      await fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ optimizationId: data.id })
      })

      alert('Model uploaded! Optimization started.')

    } catch (error) {
      console.error('Error:', error)
      alert('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <input
        type="file"
        accept=".onnx,.h5,.pth,.pt,.tflite"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        disabled={uploading}
      />

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        {uploading ? 'Uploading...' : 'Upload & Optimize'}
      </button>
    </div>
  )
}
```

### Optimization API (app/api/optimize/route.ts)
```typescript
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(request: NextRequest) {
  const { optimizationId } = await request.json()

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )

  // Get optimization record
  const { data: optimization } = await supabase
    .from('optimizations')
    .select('*')
    .eq('id', optimizationId)
    .single()

  if (!optimization) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  // Trigger GitHub Actions workflow or Modal function
  // Option 1: GitHub Actions
  await fetch('https://api.github.com/repos/YOUR_REPO/actions/workflows/optimize.yml/dispatches', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ref: 'main',
      inputs: {
        optimization_id: optimizationId,
        model_path: optimization.original_model_path
      }
    })
  })

  // Option 2: Modal (serverless Python)
  // await fetch('https://YOUR_MODAL_ENDPOINT/optimize', { ... })

  return NextResponse.json({ success: true })
}
```

---

## 🤖 GitHub Actions Worker (.github/workflows/optimize.yml)

```yaml
name: Optimize Model

on:
  workflow_dispatch:
    inputs:
      optimization_id:
        required: true
      model_path:
        required: true

jobs:
  optimize:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e .

      - name: Download model from Supabase
        run: |
          # Download using Supabase API
          curl -H "Authorization: Bearer ${{ secrets.SUPABASE_KEY }}" \
            "${{ secrets.SUPABASE_URL }}/storage/v1/object/models-original/${{ github.event.inputs.model_path }}" \
            -o input_model.onnx

      - name: Run optimization
        run: |
          modelblaze optimize input_model.onnx \
            --target mobile \
            --level high \
            --output optimized_model.onnx \
            --report json \
            --report-path report.json

      - name: Upload results to Supabase
        run: |
          # Upload optimized model
          # Update database with results
          python scripts/upload_results.py \
            --optimization-id ${{ github.event.inputs.optimization_id }} \
            --model optimized_model.onnx \
            --report report.json
```

---

## 💳 Stripe Integration

### Create Products
```bash
# In Stripe Dashboard:
1. Create product "ModelBlaze Pro" - $10/month
2. Create product "ModelBlaze Business" - $25/month
3. Copy price IDs
```

### Checkout (app/api/stripe/checkout/route.ts)
```typescript
import Stripe from 'stripe'
import { NextRequest, NextResponse } from 'next/server'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(request: NextRequest) {
  const { priceId, userId } = await request.json()

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_URL}/dashboard?success=true`,
    cancel_url: `${process.env.NEXT_PUBLIC_URL}/pricing`,
    client_reference_id: userId,
  })

  return NextResponse.json({ url: session.url })
}
```

---

## 🚀 Deployment (5 minutes)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Add environment variables in Vercel dashboard
```

### 3. Done! 🎉
Your app is live at: `https://modelblaze.vercel.app`

---

## 💰 Cost Breakdown

```
Supabase Pro:    $25/month  (500GB storage, 100GB bandwidth)
Vercel:          $0/month   (100GB bandwidth free)
GitHub Actions:  $0/month   (2,000 minutes free)
Stripe:          2.9% + $0.30 per transaction
Domain:          $12/year   (optional)

Total: $25-30/month + transaction fees
```

**Breakeven: 3 paying users ($30/month)**

---

## 📈 Scaling

When you grow:

```
0-100 users:     Supabase Pro ($25) + Vercel Free
100-1000 users:  Supabase Pro ($25) + Vercel Pro ($20)
1000+ users:     Supabase Team ($599) + Vercel Pro ($20)
                 Or migrate to your own infrastructure
```

---

Bu çok daha gerçekçi! Şimdi istersen web versiyonunu da başlatabiliriz? 🚀
