import re

class Sanitizer:
    """Handles scrubbing of sensitive info before DB insertion."""

    @staticmethod
    def strip_secrets(text: str) -> str:
        """
        Scrubs sensitive information from the given text.
        Includes patterns for major AI providers and generic high-entropy strings.
        """
        if not text:
            return ""
            
        patterns = {
            "AWS": r'AKIA[0-9A-Z]{16}',
            "GCP": r'AIza[0-9A-Za-z_-]{35}',
            "OpenAI": r'sk-[a-zA-Z0-9]{48}',
            "Anthropic": r'sk-ant-api03-[a-zA-Z0-9\-_]{93}',
            "Stripe": r'sk_live_[0-9a-zA-Z]{24}',
            "Generic_Secret": r'(?i)(password|secret|key|token|auth|credential|api_key|private_key)["\s:]+([A-Za-z0-9\-\._~\+\/]{20,})',
        }

        for label, pattern in patterns.items():
            if label == "Generic_Secret":
                # For generic secrets, we preserve the label but scrub the value
                text = re.sub(pattern, r'\1: [SCRUBBED]', text)
            else:
                text = re.sub(pattern, f'[SCRUBBED_{label}]', text)

        # Path scrubbing: only absolute paths that look like they belong to a user's home.
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
