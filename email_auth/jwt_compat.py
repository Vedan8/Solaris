import importlib

def get_jwt_exceptions():
    try:
        # Try to import from the current jwt library
        from jwt import exceptions
        
        # If InvalidKeyError doesn't exist, create a fallback
        if not hasattr(exceptions, 'InvalidKeyError'):
            class InvalidKeyError(exceptions.PyJWTError):
                """Fallback for InvalidKeyError if not in current JWT version."""
                pass
        
        return exceptions
    except ImportError:
        # Fallback if jwt import fails
        class FallbackExceptions:
            class InvalidKeyError(Exception):
                """Fallback InvalidKeyError if jwt import fails."""
                pass
        
        return FallbackExceptions

# Dynamically patch the exceptions
jwt_exceptions = get_jwt_exceptions()