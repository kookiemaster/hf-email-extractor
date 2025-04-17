"""
Browser integration using browser-use.com
"""
import requests
import json
import time
from config import ANTHROPIC_API_KEY, OPENAI_API_KEY

class BrowserUse:
    def __init__(self):
        self.base_url = "https://browser-use.com/api"
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": ANTHROPIC_API_KEY  # Using Anthropic API key for browser-use
        }
    
    def start_session(self):
        """Start a new browser session"""
        try:
            response = requests.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json={}
            )
            response.raise_for_status()
            self.session_id = response.json().get("sessionId")
            return self.session_id
        except Exception as e:
            print(f"Error starting browser session: {e}")
            return None
    
    def navigate(self, url):
        """Navigate to a URL"""
        if not self.session_id:
            self.start_session()
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions/{self.session_id}/navigate",
                headers=self.headers,
                json={"url": url}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return None
    
    def get_page_content(self):
        """Get the current page content"""
        if not self.session_id:
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/sessions/{self.session_id}/content",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting page content: {e}")
            return None
    
    def click(self, selector):
        """Click on an element using CSS selector"""
        if not self.session_id:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions/{self.session_id}/click",
                headers=self.headers,
                json={"selector": selector}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error clicking element {selector}: {e}")
            return None
    
    def type(self, selector, text):
        """Type text into an element using CSS selector"""
        if not self.session_id:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions/{self.session_id}/type",
                headers=self.headers,
                json={"selector": selector, "text": text}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error typing into element {selector}: {e}")
            return None
    
    def download_pdf(self, url, save_path):
        """Download a PDF file from a URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return save_path
        except Exception as e:
            print(f"Error downloading PDF from {url}: {e}")
            return None
    
    def close_session(self):
        """Close the browser session"""
        if not self.session_id:
            return None
        
        try:
            response = requests.delete(
                f"{self.base_url}/sessions/{self.session_id}",
                headers=self.headers
            )
            response.raise_for_status()
            self.session_id = None
            return response.json()
        except Exception as e:
            print(f"Error closing browser session: {e}")
            return None
