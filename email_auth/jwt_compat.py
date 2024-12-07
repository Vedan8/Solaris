import jwt

# Create explicit fallback exceptions
class InvalidKeyError(Exception):
    """Fallback InvalidKeyError."""
    pass

class InvalidAlgorithmError(Exception):
    """Fallback InvalidAlgorithmError."""
    pass

class InvalidTokenError(Exception):
    """Fallback InvalidTokenError."""
    pass

# Attempt to import actual exceptions from jwt library
try:
    from jwt.exceptions import InvalidKeyError as JWTInvalidKeyError
    from jwt.exceptions import InvalidAlgorithmError as JWTInvalidAlgorithmError
    from jwt.exceptions import InvalidTokenError as JWTInvalidTokenError
    
    # Override fallback exceptions if library exceptions exist
    InvalidKeyError = JWTInvalidKeyError
    InvalidAlgorithmError = JWTInvalidAlgorithmError
    InvalidTokenError = JWTInvalidTokenError
except ImportError:
    # Use fallback exceptions if import fails
    pass