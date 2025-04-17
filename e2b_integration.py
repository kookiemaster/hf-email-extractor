"""
E2B integration for terminal and code execution
"""
import requests
import json
import time
import os
from config import E2B_API_KEY

class E2BIntegration:
    def __init__(self):
        self.api_key = E2B_API_KEY
        self.base_url = "https://api.e2b.dev/v1"
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def start_session(self, template="base"):
        """Start a new e2b session"""
        try:
            response = requests.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json={"template": template}
            )
            response.raise_for_status()
            self.session_id = response.json().get("id")
            return self.session_id
        except Exception as e:
            print(f"Error starting e2b session: {e}")
            return None
    
    def execute_command(self, command):
        """Execute a shell command"""
        if not self.session_id:
            self.start_session()
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions/{self.session_id}/terminal/execute",
                headers=self.headers,
                json={"command": command}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error executing command: {e}")
            return None
    
    def create_file(self, path, content):
        """Create a file with content"""
        if not self.session_id:
            self.start_session()
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions/{self.session_id}/filesystem/write",
                headers=self.headers,
                json={"path": path, "content": content}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating file: {e}")
            return None
    
    def read_file(self, path):
        """Read a file's content"""
        if not self.session_id:
            self.start_session()
        
        try:
            response = requests.get(
                f"{self.base_url}/sessions/{self.session_id}/filesystem/read",
                headers=self.headers,
                params={"path": path}
            )
            response.raise_for_status()
            return response.json().get("content")
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def close_session(self):
        """Close the e2b session"""
        if not self.session_id:
            return None
        
        try:
            response = requests.delete(
                f"{self.base_url}/sessions/{self.session_id}",
                headers=self.headers
            )
            response.raise_for_status()
            self.session_id = None
            return True
        except Exception as e:
            print(f"Error closing e2b session: {e}")
            return None
