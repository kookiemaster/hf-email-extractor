"""
Error handling and validation utilities for the Hugging Face Contributor Email Extractor
"""
import re
import os
from typing import Dict, List, Optional, Union, Any

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def validate_repository_path(repo_path: str) -> bool:
    """
    Validate a Hugging Face repository path
    
    Args:
        repo_path (str): Repository path to validate
        
    Returns:
        bool: True if valid, raises ValidationError otherwise
    """
    if not repo_path:
        raise ValidationError("Repository path cannot be empty")
    
    # Check format (owner/repo)
    if not re.match(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$', repo_path):
        raise ValidationError("Invalid repository path format. Expected format: owner/repo")
    
    return True

def validate_email(email: str) -> bool:
    """
    Validate an email address
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def is_placeholder_email(email: str, name: str = "") -> bool:
    """
    Check if an email is likely a placeholder
    
    Args:
        email (str): Email address
        name (str, optional): Contributor name
        
    Returns:
        bool: True if email is likely a placeholder, False otherwise
    """
    # Common placeholder patterns
    placeholder_patterns = [
        r'^noreply@',
        r'^no-reply@',
        r'^donotreply@',
        r'^do-not-reply@',
        r'^admin@',
        r'^support@',
        r'^info@',
        r'^contact@',
        r'^team@',
        r'^hello@',
        r'^research@',
        r'^dev@',
        r'^development@',
        r'^github@',
        r'^git@',
        r'^huggingface@',
        r'^hf@'
    ]
    
    # Check if email matches any placeholder pattern
    for pattern in placeholder_patterns:
        if re.match(pattern, email.lower()):
            return True
    
    # Check if email domain matches company name
    if name:
        name_parts = name.lower().split()
        for part in name_parts:
            if len(part) > 3 and part in email.lower():
                domain = email.split('@')[-1].split('.')[0]
                if part == domain:
                    return True
    
    return False

def safe_file_path(base_dir: str, filename: str) -> str:
    """
    Create a safe file path that doesn't allow directory traversal
    
    Args:
        base_dir (str): Base directory
        filename (str): Filename
        
    Returns:
        str: Safe file path
    """
    # Remove any directory traversal attempts
    safe_filename = os.path.basename(filename)
    
    # Ensure base_dir exists
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    return os.path.join(base_dir, safe_filename)

def handle_api_error(error: Exception) -> Dict[str, str]:
    """
    Handle API errors and return appropriate response
    
    Args:
        error (Exception): Exception to handle
        
    Returns:
        Dict[str, str]: Error response
    """
    if isinstance(error, ValidationError):
        return {"status": "error", "message": error.message}
    else:
        return {"status": "error", "message": f"An unexpected error occurred: {str(error)}"}

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        input_str (str): Input string to sanitize
        
    Returns:
        str: Sanitized string
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[;&|`$]', '', input_str)
    return sanitized
