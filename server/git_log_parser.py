"""
Git log parser to extract contributor information
"""
import os
import re
import subprocess
import json
from datetime import datetime

class GitLogParser:
    def __init__(self, repo_dir):
        """
        Initialize the GitLogParser
        
        Args:
            repo_dir (str): Path to the git repository directory
        """
        self.repo_dir = repo_dir
    
    def extract_contributors(self):
        """
        Extract contributors from git log
        
        Returns:
            list: List of contributor information
        """
        try:
            # Change to repository directory
            os.chdir(self.repo_dir)
            
            # Run git log command to get contributors
            git_log_cmd = "git log --format='%an|%ae|%ad|%H'"
            process = subprocess.Popen(
                git_log_cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"Error running git log: {stderr.decode('utf-8')}")
                return []
            
            # Parse the output
            contributors = {}
            for line in stdout.decode('utf-8').splitlines():
                if not line.strip():
                    continue
                
                parts = line.strip("'").split('|')
                if len(parts) < 4:
                    continue
                
                name, email, date_str, commit_hash = parts
                
                # Skip placeholder emails
                if self._is_placeholder_email(email, name):
                    email = ""
                
                if name not in contributors:
                    contributors[name] = {
                        "name": name,
                        "email": email,
                        "commits": [],
                        "first_commit_date": date_str,
                        "last_commit_date": date_str
                    }
                
                # Add commit information
                contributors[name]["commits"].append(commit_hash)
                
                # Update dates if needed
                try:
                    current_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y %z")
                    first_date = datetime.strptime(contributors[name]["first_commit_date"], "%a %b %d %H:%M:%S %Y %z")
                    last_date = datetime.strptime(contributors[name]["last_commit_date"], "%a %b %d %H:%M:%S %Y %z")
                    
                    if current_date < first_date:
                        contributors[name]["first_commit_date"] = date_str
                    if current_date > last_date:
                        contributors[name]["last_commit_date"] = date_str
                except Exception as e:
                    print(f"Error parsing dates: {e}")
            
            # Convert to list and add commit count
            result = []
            for name, data in contributors.items():
                data["commit_count"] = len(data["commits"])
                result.append(data)
            
            # Sort by commit count (descending)
            result.sort(key=lambda x: x["commit_count"], reverse=True)
            
            return result
        
        except Exception as e:
            print(f"Error extracting contributors: {e}")
            return []
    
    def _is_placeholder_email(self, email, name):
        """
        Check if an email is likely a placeholder
        
        Args:
            email (str): Email address
            name (str): Contributor name
            
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
        name_parts = name.lower().split()
        for part in name_parts:
            if len(part) > 3 and part in email.lower():
                domain = email.split('@')[-1].split('.')[0]
                if part == domain:
                    return True
        
        return False
    
    def get_commit_details(self, commit_hash):
        """
        Get details for a specific commit
        
        Args:
            commit_hash (str): Commit hash
            
        Returns:
            dict: Commit details
        """
        try:
            # Change to repository directory
            os.chdir(self.repo_dir)
            
            # Run git show command to get commit details
            git_show_cmd = f"git show {commit_hash} --name-status --format='%an|%ae|%ad|%s'"
            process = subprocess.Popen(
                git_show_cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"Error running git show: {stderr.decode('utf-8')}")
                return None
            
            # Parse the output
            lines = stdout.decode('utf-8').splitlines()
            if not lines:
                return None
            
            # First line contains commit info
            parts = lines[0].strip("'").split('|')
            if len(parts) < 4:
                return None
            
            name, email, date_str, subject = parts
            
            # Extract changed files
            changed_files = []
            for line in lines[1:]:
                if line.strip() and '\t' in line:
                    status, file_path = line.strip().split('\t', 1)
                    changed_files.append({
                        "status": status,
                        "path": file_path
                    })
            
            return {
                "hash": commit_hash,
                "author": name,
                "email": email,
                "date": date_str,
                "subject": subject,
                "changed_files": changed_files
            }
        
        except Exception as e:
            print(f"Error getting commit details: {e}")
            return None
