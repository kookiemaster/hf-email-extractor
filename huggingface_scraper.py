"""
GitHub repository scraper for Hugging Face
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time

class HuggingFaceScraper:
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
    
    def get_git_commits_url(self, repo_path):
        """
        Get the URL for the commits page of a repository
        
        Args:
            repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
            
        Returns:
            str: Commits URL
        """
        return f"{self.base_url}/{repo_path}/commits/main"
    
    def get_contributors_url(self, repo_path):
        """
        Get the URL for the contributors page of a repository
        
        Args:
            repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
            
        Returns:
            str: Contributors URL
        """
        return f"{self.base_url}/{repo_path}/contributors"
    
    def extract_contributors_from_page(self, html_content):
        """
        Extract contributors from the HTML content of the contributors page
        
        Args:
            html_content (str): HTML content of the contributors page
            
        Returns:
            list: List of contributor information
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        contributors = []
        
        # Find contributor elements
        contributor_elements = soup.find_all('a', href=re.compile(r'^/[^/]+$'))
        
        for element in contributor_elements:
            username = element['href'].strip('/')
            name_elem = element.find('span', class_='font-bold')
            name = name_elem.get_text(strip=True) if name_elem else username
            
            contributors.append({
                "username": username,
                "name": name,
                "profile_url": f"{self.base_url}{element['href']}"
            })
        
        return contributors
    
    def extract_commits_from_page(self, html_content):
        """
        Extract commits from the HTML content of the commits page
        
        Args:
            html_content (str): HTML content of the commits page
            
        Returns:
            list: List of commit information
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        commits = []
        
        # Find commit elements
        commit_elements = soup.find_all('div', class_='flex flex-col space-y-4')
        
        for element in commit_elements:
            commit_link = element.find('a', href=re.compile(r'/commit/'))
            if not commit_link:
                continue
                
            commit_hash = commit_link['href'].split('/')[-1]
            
            # Extract author information
            author_elem = element.find('span', class_='font-bold')
            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
            
            # Extract commit message
            message_elem = element.find('p', class_='break-words')
            message = message_elem.get_text(strip=True) if message_elem else ""
            
            # Extract date
            date_elem = element.find('time')
            date = date_elem['datetime'] if date_elem and 'datetime' in date_elem.attrs else ""
            
            commits.append({
                "hash": commit_hash,
                "author": author,
                "message": message,
                "date": date,
                "url": f"{self.base_url}{commit_link['href']}"
            })
        
        return commits
    
    def clone_repository(self, repo_path, target_dir):
        """
        Clone a repository to the target directory
        
        Args:
            repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
            target_dir (str): Target directory to clone the repository to
            
        Returns:
            bool: True if successful, False otherwise
        """
        git_url = f"{self.base_url}/{repo_path}.git"
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
