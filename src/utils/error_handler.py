"""
Error Handler - Centralized and secure error handling
Prevents information disclosure while maintaining debugging capability
"""

import logging
from typing import Optional, Type


class ModelBlazeError(Exception):
    """Base exception class for ModelBlaze"""
    pass


class ModelLoadError(ModelBlazeError):
    """Error loading model"""
    pass


class OptimizationError(ModelBlazeError):
    """Error during optimization"""
    pass


class ValidationError(ModelBlazeError):
    """Input validation error"""
    pass


class ErrorHandler:
    """
    Centralized error handler for secure error management

    Prevents information disclosure by showing generic messages to users
    while logging detailed error information for debugging.
    """

    # Mapping of exception types to user-friendly messages
    ERROR_MESSAGES = {
        FileNotFoundError: "Model dosyası bulunamadı. Lütfen geçerli bir dosya yolu sağlayın.",
        PermissionError: "Dosya erişim izni reddedildi. Lütfen dosya izinlerini kontrol edin.",
        ImportError: "Gerekli kütüphane kurulu değil. Lütfen requirements.txt dosyasını kontrol edin.",
        ValueError: "Geçersiz parametre değeri. Lütfen girdilerinizi kontrol edin.",
        RuntimeError: "İşlem sırasında bir hata oluştu. Lütfen tekrar deneyin.",
        MemoryError: "Yetersiz bellek. Daha küçük bir model kullanmayı deneyin.",
        KeyboardInterrupt: "İşlem kullanıcı tarafından iptal edildi.",
    }

    @staticmethod
    def handle_error(
        error: Exception,
        user_message: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        error_type: Type[Exception] = ModelBlazeError
    ) -> str:
        """
        Güvenli hata yönetimi

        Args:
            error: Yakalanan exception
            user_message: Kullanıcıya gösterilecek özel mesaj (opsiyonel)
            logger: Log için kullanılacak logger (opsiyonel)
            error_type: Wrap edilecek exception tipi

        Returns:
            Kullanıcı dostu hata mesajı
        """
        # Detaylı hatayı loglara yaz (sadece sunucuda/dosyada görülür)
        if logger:
            logger.error(
                f"Internal error: {type(error).__name__}: {str(error)}",
                exc_info=True
            )

        # Kullanıcıya gösterilecek mesajı belirle
        if user_message:
            safe_message = user_message
        else:
            # Exception tipine göre generic mesaj
            safe_message = ErrorHandler.ERROR_MESSAGES.get(
                type(error),
                "Beklenmeyen bir hata oluştu. Lütfen log dosyalarını kontrol edin."
            )

        return safe_message

    @staticmethod
    def wrap_import_error(error: ImportError) -> str:
        """
        ImportError için özel mesaj oluştur

        Args:
            error: ImportError exception

        Returns:
            Kullanıcı dostu mesaj
        """
        error_msg = str(error).lower()

        if 'tensorflow' in error_msg:
            return "TensorFlow kurulu değil. Lütfen 'pip install tensorflow>=2.13.0' komutunu çalıştırın."
        elif 'torch' in error_msg:
            return "PyTorch kurulu değil. Lütfen 'pip install torch>=2.0.0' komutunu çalıştırın."
        elif 'onnx' in error_msg:
            return "ONNX kurulu değil. Lütfen 'pip install onnx onnxruntime' komutunu çalıştırın."
        elif 'tensorflow_model_optimization' in error_msg or 'tfmot' in error_msg:
            return "TensorFlow Model Optimization kurulu değil. Lütfen 'pip install tensorflow-model-optimization' komutunu çalıştırın."
        else:
            return f"Gerekli kütüphane kurulu değil: {error.name if hasattr(error, 'name') else 'bilinmiyor'}"

    @staticmethod
    def handle_framework_error(error: Exception, framework: str, logger: Optional[logging.Logger] = None) -> str:
        """
        Framework-specific error handling

        Args:
            error: Exception
            framework: Framework name (tensorflow, pytorch, onnx)
            logger: Logger instance

        Returns:
            User-friendly error message
        """
        if logger:
            logger.error(f"{framework} error: {type(error).__name__}: {str(error)}", exc_info=True)

        if isinstance(error, ImportError):
            return ErrorHandler.wrap_import_error(error)
        elif isinstance(error, (RuntimeError, ValueError)):
            return f"{framework.capitalize()} işlemi başarısız oldu. Model formatı desteklenmiyor olabilir."
        else:
            return f"{framework.capitalize()} ile ilgili bir hata oluştu."
