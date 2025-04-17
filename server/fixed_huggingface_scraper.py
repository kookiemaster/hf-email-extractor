"""
Fixed repository scraper for Hugging Face
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
import tempfile

class FixedHuggingFaceScraper:
    def __init__(self):
        self.base_url = "https://huggingface.co"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def get_repository_info(self, repo_path):
        """
        Get basic information about a Hugging Face repository
        
        Args:
            repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
            
        Returns:
            dict: Repository information
        """
        url = f"{self.base_url}/{repo_path}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract repository name and owner
            repo_info = {
                "full_path": repo_path,
                "owner": repo_path.split('/')[0],
                "name": repo_path.split('/')[1],
                "url": url,
                "git_url": f"{self.base_url}/{repo_path}.git"
            }
            
            # Extract description if available
            description_elem = soup.find('div', class_='prose')
            if description_elem:
                repo_info["description"] = description_elem.get_text(strip=True)
            
            return repo_info
        except Exception as e:
            print(f"Error getting repository info for {repo_path}: {e}")
            return None
    
    def clone_repository(self, repo_path, target_dir=None):
        """
        Clone a repository to the target directory
        
        Args:
            repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
            target_dir (str, optional): Target directory to clone the repository to.
                                       If None, a temporary directory will be created.
            
        Returns:
            str: Path to the cloned repository directory if successful, None otherwise
        """
        git_url = f"{self.base_url}/{repo_path}.git"
        
        # If no target directory is provided, create a temporary one
        if target_dir is None:
            target_dir = tempfile.mkdtemp()
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        clone_dir = os.path.join(target_dir, repo_path.split('/')[-1])
        
        try:
            # Use os.system to run git clone command
            result = os.system(f"git clone {git_url} {clone_dir}")
            
            if result == 0:
                return clone_dir
            else:
                print(f"Error cloning repository {repo_path}")
                return None
        except Exception as e:
            print(f"Error cloning repository {repo_path}: {e}")
            return None
    
    def get_contributors(self, repo_path):
        """
        Get contributors for a repository without cloning
        
        Args:
            repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
            
        Returns:
            list: List of contributor information
        """
        url = f"{self.base_url}/{repo_path}/commits/main"
        contributors = {}
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find commit elements - try different selectors for different page structures
            commit_elements = soup.find_all('div', class_='flex flex-col space-y-4')
            
            # If no commit elements found with the first selector, try alternatives
            if not commit_elements:
                # Try finding commit table rows
                commit_elements = soup.find_all('tr')
            
            for element in commit_elements:
                # Extract author information - try different selectors
                author_elem = element.find('a', class_='font-bold')
                
                # If not found, try alternative selectors
                if not author_elem:
                    author_elem = element.find('a', href=re.compile(r'^/[^/]+$'))
                
                if not author_elem:
                    # Try finding any author-like element
                    for a_tag in element.find_all('a'):
                        if a_tag.get_text(strip=True) and not a_tag.get('href', '').startswith('/commit/'):
                            author_elem = a_tag
                            break
                
                if not author_elem:
                    continue
                    
                author = author_elem.get_text(strip=True)
                
                # Extract date
                date_elem = element.find('time')
                date = date_elem['datetime'] if date_elem and 'datetime' in date_elem.attrs else ""
                
                # Add to contributors dict
                if author not in contributors:
                    contributors[author] = {
                        "name": author,
                        "commit_count": 1,
                        "first_commit_date": date,
                        "last_commit_date": date
                    }
                else:
                    contributors[author]["commit_count"] += 1
                    
                    # Update first/last commit dates
                    if date < contributors[author]["first_commit_date"]:
                        contributors[author]["first_commit_date"] = date
                    if date > contributors[author]["last_commit_date"]:
                        contributors[author]["last_commit_date"] = date
            
            return list(contributors.values())
        
        except Exception as e:
            print(f"Error getting contributors for {repo_path}: {e}")
            return []
