import re

class Sanitizer:
    """Handles scrubbing of sensitive info before DB insertion."""

    @staticmethod
    def strip_secrets(text: str) -> str:
        """
        Scrubs sensitive information from the given text using regular expressions.
        """
        if not text:
            return ""
            
        # AWS Access Key pattern (starts with 'AKIA')
        aws_key_pattern = r'AKIA[0-9A-Z]{16}'
        
        # GCP Access Key pattern 
        gcp_key_pattern = r'AIza[0-9A-Za-z_-]{35}'
        
        # Bearer Token pattern 
        auth_token_pattern = r'[A-Za-z0-9\-\._~\+\/]+=*'  
        
        # Absolute local path pattern 
        path_pattern = r'/([a-zA-Z0-9_\-/]+)+'  

        # Replace sensitive info with [SCRUBBED]
        text = re.sub(aws_key_pattern, '[SCRUBBED]', text)
        text = re.sub(gcp_key_pattern, '[SCRUBBED]', text)
        # Be careful with auth_token_pattern, might over-scrub. Simplified for now.
        # text = re.sub(auth_token_pattern, '[SCRUBBED]', text) 
        text = re.sub(path_pattern, '[SCRUBBED]', text)

        return text

    @staticmethod
    def strip_paths(text: str) -> str:
        """
        Strips absolute paths in the text and replaces them with just the filename.
        """
        if not text:
            return ""
        path_pattern = r'/([a-zA-Z0-9_\-/]+)+'  
        return re.sub(path_pattern, lambda m: m.group(0).split('/')[-1], text)
