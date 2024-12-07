import importlib

def get_jwt_exceptions():
    try:
        # Try to import from the current jwt library
        from jwt import exceptions
        
        # Create a base error class if PyJWTError doesn't exist
        if not hasattr(exceptions, 'PyJWTError'):
            class PyJWTError(Exception):
                """Fallback base error for JWT exceptions."""
                pass
        
        # Create InvalidKeyError if it doesn't exist
        if not hasattr(exceptions, 'InvalidKeyError'):
            class InvalidKeyError(Exception):
                """Fallback for InvalidKeyError."""
                pass
        
        return exceptions
    except ImportError:
        # Fallback class if import fails
        class FallbackExceptions:
            class PyJWTError(Exception):
                """Fallback base error."""
                pass
            
            class InvalidKeyError(PyJWTError):
                """Fallback InvalidKeyError."""
                pass
        
        return FallbackExceptions

# Dynamically patch the exceptions
jwt_exceptions = get_jwt_exceptions()