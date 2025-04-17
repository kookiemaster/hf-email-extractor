"""
Alternative email search functionality that doesn't rely on browser automation
"""
import re
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
import PyPDF2
from urllib.parse import quote_plus

class AlternativeEmailSearcher:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.pdf_dir = os.path.join(os.getcwd(), "pdfs")
        
        # Create PDF directory if it doesn't exist
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
    
    def search_for_email(self, name, affiliation=None):
        """
        Search for email address of a contributor using direct HTTP requests
        
        Args:
            name (str): Contributor name
            affiliation (str, optional): Contributor affiliation
            
        Returns:
            dict: Search results including potential email addresses
        """
        results = {
            "name": name,
            "affiliation": affiliation,
            "potential_emails": [],
            "sources": [],
            "most_likely_email": None
        }
        
        # Try different search strategies
        self._search_dblp(name, results)
        
        if not results["potential_emails"]:
            self._search_arxiv(name, results)
        
        if not results["potential_emails"] and affiliation:
            self._search_university_directory(name, affiliation, results)
        
        # Determine most likely email
        if results["potential_emails"]:
            # Sort by frequency and prefer academic emails
            email_counts = {}
            for email in results["potential_emails"]:
                if email in email_counts:
                    email_counts[email] += 1
                else:
                    email_counts[email] = 1
            
            # Prioritize academic emails
            academic_emails = [email for email in results["potential_emails"] if self._is_academic_email(email)]
            
            if academic_emails:
                # Sort academic emails by frequency
                academic_emails.sort(key=lambda x: email_counts[x], reverse=True)
                results["most_likely_email"] = academic_emails[0]
            else:
                # Sort all emails by frequency
                sorted_emails = sorted(email_counts.items(), key=lambda x: x[1], reverse=True)
                results["most_likely_email"] = sorted_emails[0][0]
        
        return results
    
    def _search_dblp(self, name, results):
        """
        Search for email on DBLP (computer science bibliography)
        
        Args:
            name (str): Contributor name
            results (dict): Results dictionary to update
        """
        try:
            # Format search query
            query = quote_plus(name)
            url = f"https://dblp.org/search?q={query}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find author links
                author_links = []
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    if "/pid/" in href and "dblp.org" in href:
                        author_links.append(href)
                
                # Visit author page
                if author_links:
                    author_url = author_links[0]
                    author_response = requests.get(author_url, headers=self.headers)
                    
                    if author_response.status_code == 200:
                        author_soup = BeautifulSoup(author_response.text, "html.parser")
                        
                        # Look for paper links
                        paper_links = []
                        for a_tag in author_soup.find_all("a", href=True):
                            href = a_tag.get("href", "")
                            if ".pdf" in href or "doi.org" in href or "arxiv.org" in href:
                                paper_links.append(href)
                        
                        # Process up to 3 paper links
                        for i, link in enumerate(paper_links[:3]):
                            try:
                                if ".pdf" in link:
                                    # Download and process PDF
                                    pdf_path = os.path.join(self.pdf_dir, f"{name.replace(' ', '_')}_{i}.pdf")
                                    self._download_pdf(link, pdf_path)
                                    self._extract_emails_from_pdf(pdf_path, results)
                                else:
                                    # Visit paper page
                                    paper_response = requests.get(link, headers=self.headers)
                                    
                                    if paper_response.status_code == 200:
                                        paper_soup = BeautifulSoup(paper_response.text, "html.parser")
                                        
                                        # Extract text and look for email patterns
                                        text = paper_soup.get_text()
                                        emails = re.findall(self.email_pattern, text)
                                        
                                        for email in emails:
                                            if email not in results["potential_emails"] and self._is_valid_email(email):
                                                results["potential_emails"].append(email)
                                                results["sources"].append({
                                                    "email": email,
                                                    "source": "DBLP Paper Page",
                                                    "url": link
                                                })
                            except Exception as e:
                                print(f"Error processing paper link {link}: {e}")
        
        except Exception as e:
            print(f"Error searching DBLP: {e}")
    
    def _search_arxiv(self, name, results):
        """
        Search for email on arXiv
        
        Args:
            name (str): Contributor name
            results (dict): Results dictionary to update
        """
        try:
            # Format search query
            query = quote_plus(f"au:{name}")
            url = f"https://export.arxiv.org/api/query?search_query={query}&start=0&max_results=5"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "xml")
                
                # Find paper links
                entries = soup.find_all("entry")
                
                for entry in entries:
                    try:
                        # Get PDF link
                        pdf_link = None
                        links = entry.find_all("link")
                        for link in links:
                            if link.get("title") == "pdf":
                                pdf_link = link.get("href")
                                break
                        
                        if pdf_link:
                            # Download and process PDF
                            pdf_path = os.path.join(self.pdf_dir, f"{name.replace(' ', '_')}_{entry.find('id').text.split('/')[-1]}.pdf")
                            self._download_pdf(pdf_link, pdf_path)
                            self._extract_emails_from_pdf(pdf_path, results)
                    
                    except Exception as e:
                        print(f"Error processing arXiv entry: {e}")
        
        except Exception as e:
            print(f"Error searching arXiv: {e}")
    
    def _search_university_directory(self, name, affiliation, results):
        """
        Search for email in university directory
        
        Args:
            name (str): Contributor name
            affiliation (str): Contributor affiliation
            results (dict): Results dictionary to update
        """
        try:
            # Format search query
            query = quote_plus(f"{name} {affiliation} email")
            url = f"https://www.google.com/search?q={query}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract text and look for email patterns
                text = soup.get_text()
                emails = re.findall(self.email_pattern, text)
                
                for email in emails:
                    if email not in results["potential_emails"] and self._is_valid_email(email):
                        results["potential_emails"].append(email)
                        results["sources"].append({
                            "email": email,
                            "source": "Google Search Results",
                            "url": url
                        })
                
                # Find result links
                result_links = []
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    if href.startswith("/url?q="):
                        url = href.split("/url?q=")[1].split("&")[0]
                        if "google.com" not in url and url not in result_links:
                            result_links.append(url)
                
                # Visit up to 3 result links
                for i, link in enumerate(result_links[:3]):
                    try:
                        link_response = requests.get(link, headers=self.headers)
                        
                        if link_response.status_code == 200:
                            link_soup = BeautifulSoup(link_response.text, "html.parser")
                            
                            # Extract text and look for email patterns
                            text = link_soup.get_text()
                            emails = re.findall(self.email_pattern, text)
                            
                            for email in emails:
                                if email not in results["potential_emails"] and self._is_valid_email(email):
                                    results["potential_emails"].append(email)
                                    results["sources"].append({
                                        "email": email,
                                        "source": "Web Page",
                                        "url": link
                                    })
                    except Exception as e:
                        print(f"Error visiting link {link}: {e}")
        
        except Exception as e:
            print(f"Error searching university directory: {e}")
    
    def _download_pdf(self, url, save_path):
        """
        Download a PDF file from a URL
        
        Args:
            url (str): URL of the PDF file
            save_path (str): Path to save the PDF file
            
        Returns:
            str: Path to the saved PDF file
        """
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return save_path
        except Exception as e:
            print(f"Error downloading PDF from {url}: {e}")
            return None
    
    def _extract_emails_from_pdf(self, pdf_path, results):
        """
        Extract emails from a PDF file
        
        Args:
            pdf_path (str): Path to PDF file
            results (dict): Results dictionary to update
        """
        try:
            if not os.path.exists(pdf_path):
                print(f"PDF file not found: {pdf_path}")
                return
            
            # Open the PDF file
            with open(pdf_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from first few pages (usually emails are in first pages)
                text = ""
                for i in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[i]
                    text += page.extract_text()
                
                # Find emails in text
                emails = re.findall(self.email_pattern, text)
                
                for email in emails:
                    if email not in results["potential_emails"] and self._is_valid_email(email):
                        results["potential_emails"].append(email)
                        results["sources"].append({
                            "email": email,
                            "source": "PDF Document",
                            "url": pdf_path
                        })
        
        except Exception as e:
            print(f"Error extracting emails from PDF: {e}")
    
    def _is_valid_email(self, email):
        """
        Check if an email is valid
        
        Args:
            email (str): Email address
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        # Basic validation
        if not re.match(self.email_pattern, email):
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'example\.com$',
            r'test\.com$',
            r'domain\.com$',
            r'email\.com$',
            r'sample\.com$',
            r'placeholder\.com$'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, email.lower()):
                return False
        
        return True
    
    def _is_academic_email(self, email):
        """
        Check if an email is from an academic institution
        
        Args:
            email (str): Email address
            
        Returns:
            bool: True if email is academic, False otherwise
        """
        academic_domains = [
            r'\.edu$',
            r'\.ac\.[a-z]{2}$',
            r'\.edu\.[a-z]{2}$',
            r'university',
            r'\.uni-[a-z]+\.[a-z]{2}$',
            r'\.college\.',
            r'\.institute\.'
        ]
        
        for domain in academic_domains:
            if re.search(domain, email.lower()):
                return True
        
        return False
