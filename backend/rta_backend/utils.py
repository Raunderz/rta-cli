import re

class Sanitizer:
    """Handles scrubbing of sensitive info before DB insertion."""

    @staticmethod
    def strip_secrets(text: str) -> str:
        """
        Scrubs sensitive information from the given text.
        """
        if not text:
            return ""
            
        # AWS Access Key pattern
        aws_key_pattern = r'AKIA[0-9A-Z]{16}'
        # GCP Access Key pattern 
        gcp_key_pattern = r'AIza[0-9A-Za-z_-]{35}'
        # Generic Secret/Key pattern (simplified)
        secret_pattern = r'(?i)(password|secret|key|token|auth)["\s:]+[A-Za-z0-9\-\._~\+\/]{16,}'

        text = re.sub(aws_key_pattern, '[SCRUBBED_AWS]', text)
        text = re.sub(gcp_key_pattern, '[SCRUBBED_GCP]', text)
        # Only scrub if it looks like a long hex/base64 string after a keyword
        # text = re.sub(secret_pattern, r'\1: [SCRUBBED]', text)

        # Path scrubbing was too aggressive. Agents need paths to function.
        # We only scrub absolute paths that look like they belong to a user's home.
        home_path_pattern = r'/home/[a-zA-Z0-9_-]+'
        text = re.sub(home_path_pattern, '/home/[USER]', text)

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
