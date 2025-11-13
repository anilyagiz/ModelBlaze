# Contributing to ModelBlaze

Thank you for your interest in contributing to ModelBlaze! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or screenshots

### Suggesting Features

We love new ideas! To suggest a feature:
- Open an issue with the "enhancement" label
- Describe the feature and its benefits
- Provide examples of how it would be used
- Explain why it would be valuable

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clear, documented code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   pytest tests/
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of your changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Explain what changes you made and why

## Development Setup

```bash
# Clone the repo
git clone https://github.com/anilyagiz/ModelBlaze.git
cd ModelBlaze

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/
```

## Code Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Write docstrings for all functions and classes
- Keep functions focused and concise
- Add comments for complex logic

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting
- Aim for high test coverage
- Test edge cases and error handling

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all new functions and classes
- Update examples if needed
- Keep documentation clear and concise

## Questions?

If you have questions, feel free to:
- Open a discussion on GitHub
- Reach out on our community channels
- Email us at contact@modelblaze.io

Thank you for contributing to ModelBlaze! 🔥
