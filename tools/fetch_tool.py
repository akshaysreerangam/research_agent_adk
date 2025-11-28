# tools/fetch_tool.py

import requests
from typing import Dict

def fetch_url(url: str) -> Dict[str, str]:
    """
    Fetches the full text content of a webpage from the given URL.
    
    This tool is used by agents to read online articles, blogs, or documentation
    when only a URL is available from search results.
    
    Args:
        url: The complete URL of the webpage to fetch (must include https://)
    
    Returns:
        Dictionary with status and fetched content or error message.
        Success: {"status": "success", "content": "full page text..."}
        Error:   {"status": "error", "error_message": "..."}
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0)"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        text = response.text

        # Truncate to safe length for Gemini context
        if len(text) > 12000:
            text = text[:12000] + "\n\n... [Content truncated to fit model limits]"

        return {
            "status": "success",
            "content": text,
            "url": url,
            "length": len(text)
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Failed to fetch {url}: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }