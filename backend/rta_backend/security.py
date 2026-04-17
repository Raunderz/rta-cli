import re

class Sanitizer:
    """Handles scrubbing of sensitive info before DB insertion."""
    
    @staticmethod
    def strip_secrets(text: str) -> str:
        # TODO: Implement RegEx stripping for AWS keys, etc.
        pass
    
    @staticmethod
    def strip_paths(text: str) -> str:
        # TODO: Convert absolute paths to filenames
        pass

def verify_hcaptcha(token: str) -> bool:
    # TODO: Implement hCaptcha verification against https://hcaptcha.com/siteverify
    pass

def validate_password_strength(password: str) -> bool:
    # TODO: minimum 10 char, uppercase, numbers, symbols
    pass

def generate_api_key() -> str:
    # TODO: return unique cryptographically secure key string
    pass
