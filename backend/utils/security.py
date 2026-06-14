import html
import logging

# Configure logging for the security audit
logging.basicConfig(level=logging.INFO)

def sanitize_and_log(content: str, channel: str) -> str:
    """Sanitizes content and logs the event for Audit/Security."""
    clean_content = html.escape(content)
    logging.info(f"SECURITY AUDIT: Data sanitized from channel={channel}. Length={len(clean_content)}")
    return clean_content