"""
Direct contributor extraction from Hugging Face repository
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
import tempfile

class DirectContributorExtractor:
    def __init__(self):
        self.base_url = "https://huggingface.co"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def extract_contributors_from_model_card(self, repo_path):
        """
        Extract contributors directly from the model card content
        
        Args:
            repo_path (str): Repository path (e.g., 'facebook/bart-large')
            
        Returns:
            list: List of contributor information
        """
        url = f"{self.base_url}/{repo_path}"
        contributors = []
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract model card content
            model_card = soup.find('div', class_='prose')
            if not model_card:
                return []
            
            # Look for author information in the model card
            text = model_card.get_text()
            
            # Extract authors from BibTeX if present
            bibtex_match = re.search(r'author\s*=\s*{([^}]+)}', text)
            if bibtex_match:
                authors_text = bibtex_match.group(1)
                # Split authors by 'and' or newline with names
                authors = re.split(r'\s+and\s+|\n\s*', authors_text)
                
                for author in authors:
                    # Clean up author name
                    author = author.strip()
                    if author:
                        contributors.append({
                            "name": author,
                            "commit_count": 1,
                            "first_commit_date": "",
                            "last_commit_date": ""
                        })
            
            # If no authors found in BibTeX, look for common author patterns
            if not contributors:
                # Look for "by [Author]" pattern
                by_matches = re.findall(r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
                for match in by_matches:
                    contributors.append({
                        "name": match,
                        "commit_count": 1,
                        "first_commit_date": "",
                        "last_commit_date": ""
                    })
                
                # Look for "Author:" pattern
                author_matches = re.findall(r'[Aa]uthor[s]?:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
                for match in author_matches:
                    contributors.append({
                        "name": match,
                        "commit_count": 1,
                        "first_commit_date": "",
                        "last_commit_date": ""
                    })
            
            # Extract from paper citation if present
            if not contributors:
                # Look for names in paper citations
                citation_matches = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+et\s+al\.', text)
                for match in citation_matches:
                    contributors.append({
                        "name": match,
                        "commit_count": 1,
                        "first_commit_date": "",
                        "last_commit_date": ""
                    })
            
            # Extract from specific model card sections
            if not contributors:
                # Try to find authors in specific sections
                sections = model_card.find_all(['h1', 'h2', 'h3', 'p'])
                for section in sections:
                    section_text = section.get_text().lower()
                    if 'author' in section_text or 'creator' in section_text or 'contributor' in section_text:
                        # Get the next paragraph which might contain names
                        next_p = section.find_next('p')
                        if next_p:
                            # Look for capitalized names
                            name_matches = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', next_p.get_text())
                            for match in name_matches:
                                contributors.append({
                                    "name": match,
                                    "commit_count": 1,
                                    "first_commit_date": "",
                                    "last_commit_date": ""
                                })
            
            # Extract from BibTeX author field
            if not contributors:
                # Look for author field in BibTeX
                author_field_match = re.search(r'author\s*=\s*{([^}]+)}', text)
                if author_field_match:
                    authors_text = author_field_match.group(1)
                    # Extract names from the author field
                    name_matches = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', authors_text)
                    for match in name_matches:
                        contributors.append({
                            "name": match,
                            "commit_count": 1,
                            "first_commit_date": "",
                            "last_commit_date": ""
                        })
            
            # Extract from paper title
            if not contributors:
                # Look for paper title with authors
                paper_title_match = re.search(r'paper\s+([^"]+)"', text)
                if paper_title_match:
                    paper_title = paper_title_match.group(1)
                    # Look for "by [Author]" pattern in paper title
                    by_matches = re.findall(r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', paper_title)
                    for match in by_matches:
                        contributors.append({
                            "name": match,
                            "commit_count": 1,
                            "first_commit_date": "",
                            "last_commit_date": ""
                        })
            
            # If still no contributors found, try to extract from the entire text
            if not contributors:
                # Look for common name patterns in the entire text
                name_matches = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
                # Filter out common non-name phrases
                common_phrases = ['Hugging Face', 'Model Card', 'Natural Language', 'Machine Learning', 'Deep Learning']
                filtered_names = [name for name in name_matches if name not in common_phrases]
                
                # Take up to 5 names to avoid too many false positives
                for match in filtered_names[:5]:
                    contributors.append({
                        "name": match,
                        "commit_count": 1,
                        "first_commit_date": "",
                        "last_commit_date": ""
                    })
            
            # Remove duplicates
            unique_contributors = []
            seen_names = set()
            for contributor in contributors:
                if contributor['name'] not in seen_names:
                    seen_names.add(contributor['name'])
                    unique_contributors.append(contributor)
            
            return unique_contributors
        
        except Exception as e:
            print(f"Error extracting contributors from model card for {repo_path}: {e}")
            return []
    
    def extract_contributors_from_paper(self, repo_path):
        """
        Extract contributors from the associated paper
        
        Args:
            repo_path (str): Repository path (e.g., 'facebook/bart-large')
            
        Returns:
            list: List of contributor information
        """
        url = f"{self.base_url}/{repo_path}"
        contributors = []
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for arxiv link
            arxiv_link = None
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href', '')
                if 'arxiv.org' in href or 'arxiv:' in href:
                    arxiv_link = href
                    break
            
            if arxiv_link:
                # Extract arxiv ID
                arxiv_id = None
                if 'arxiv.org' in arxiv_link:
                    arxiv_id = arxiv_link.split('/')[-1]
                elif 'arxiv:' in arxiv_link:
                    arxiv_id = arxiv_link.split(':')[-1]
                
                if arxiv_id:
                    # Get paper metadata from arXiv API
                    arxiv_api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
                    arxiv_response = requests.get(arxiv_api_url, headers=self.headers)
                    
                    if arxiv_response.status_code == 200:
                        arxiv_soup = BeautifulSoup(arxiv_response.text, 'xml')
                        
                        # Extract authors
                        author_tags = arxiv_soup.find_all('author')
                        for author_tag in author_tags:
                            name_tag = author_tag.find('name')
                            if name_tag:
                                contributors.append({
                                    "name": name_tag.get_text(),
                                    "commit_count": 1,
                                    "first_commit_date": "",
                                    "last_commit_date": ""
                                })
            
            return contributors
        
        except Exception as e:
            print(f"Error extracting contributors from paper for {repo_path}: {e}")
            return []
    
    def extract_contributors_from_bibtex(self, repo_path):
        """
        Extract contributors from BibTeX citation
        
        Args:
            repo_path (str): Repository path (e.g., 'facebook/bart-large')
            
        Returns:
            list: List of contributor information
        """
        url = f"{self.base_url}/{repo_path}"
        contributors = []
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Look for BibTeX citation
            bibtex_match = re.search(r'@[a-zA-Z]+{[^}]+author\s*=\s*{([^}]+)}', response.text)
            if bibtex_match:
                authors_text = bibtex_match.group(1)
                
                # Split authors by 'and' or newline
                authors = re.split(r'\s+and\s+|\n\s*', authors_text)
                
                for author in authors:
                    # Clean up author name
                    author = author.strip()
                    if author:
                        # Handle different BibTeX name formats
                        if ',' in author:
                            # Last name, First name format
                            parts = author.split(',')
                            if len(parts) >= 2:
                                name = f"{parts[1].strip()} {parts[0].strip()}"
                                contributors.append({
                                    "name": name,
                                    "commit_count": 1,
                                    "first_commit_date": "",
                                    "last_commit_date": ""
                                })
                        else:
                            # First name Last name format
                            contributors.append({
                                "name": author,
                                "commit_count": 1,
                                "first_commit_date": "",
                                "last_commit_date": ""
                            })
            
            return contributors
        
        except Exception as e:
            print(f"Error extracting contributors from BibTeX for {repo_path}: {e}")
            return []
    
    def get_contributors(self, repo_path):
        """
        Get contributors for a repository using multiple methods
        
        Args:
            repo_path (str): Repository path (e.g., 'facebook/bart-large')
            
        Returns:
            list: List of contributor information
        """
        # Try different methods to extract contributors
        contributors = []
        
        # Method 1: Extract from model card
        model_card_contributors = self.extract_contributors_from_model_card(repo_path)
        contributors.extend(model_card_contributors)
        
        # Method 2: Extract from paper
        if not contributors:
            paper_contributors = self.extract_contributors_from_paper(repo_path)
            contributors.extend(paper_contributors)
        
        # Method 3: Extract from BibTeX
        if not contributors:
            bibtex_contributors = self.extract_contributors_from_bibtex(repo_path)
            contributors.extend(bibtex_contributors)
        
        # Remove duplicates
        unique_contributors = []
        seen_names = set()
        for contributor in contributors:
            if contributor['name'] not in seen_names:
                seen_names.add(contributor['name'])
                unique_contributors.append(contributor)
        
        return unique_contributors
