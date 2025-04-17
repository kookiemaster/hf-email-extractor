"""
Email search functionality to find contributor email addresses
"""
import re
import requests
from bs4 import BeautifulSoup
import time
import random
from browser_integration import BrowserUse
from config import ANTHROPIC_API_KEY, OPENAI_API_KEY
import PyPDF2
import os
import json

class EmailSearcher:
    def __init__(self):
        self.browser = BrowserUse()
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
        Search for email address of a contributor
        
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
        self._search_google_scholar(name, affiliation, results)
        
        if not results["potential_emails"]:
            self._search_general_web(name, affiliation, results)
        
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
    
    def _search_google_scholar(self, name, affiliation, results):
        """
        Search for email on Google Scholar
        
        Args:
            name (str): Contributor name
            affiliation (str): Contributor affiliation
            results (dict): Results dictionary to update
        """
        try:
            # Format search query
            query = f"{name}"
            if affiliation:
                query += f" {affiliation}"
            
            # Start browser session
            self.browser.start_session()
            
            # Navigate to Google Scholar
            self.browser.navigate("https://scholar.google.com/")
            time.sleep(2)
            
            # Get page content
            content = self.browser.get_page_content()
            
            # Find search input and submit search
            search_input_selector = "input[name='q']"
            self.browser.type(search_input_selector, query)
            time.sleep(1)
            
            # Press Enter to search
            search_button_selector = "button[type='submit']"
            self.browser.click(search_button_selector)
            time.sleep(3)
            
            # Get search results
            content = self.browser.get_page_content()
            
            if content:
                # Parse content
                soup = BeautifulSoup(content.get("html", ""), "html.parser")
                
                # Find paper links
                paper_links = []
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    # Look for PDF links or paper links
                    if ".pdf" in href or "scholar.google.com/citations" in href:
                        paper_links.append(href)
                    elif "/scholar?cluster=" in href:
                        paper_links.append(f"https://scholar.google.com{href}")
                
                # Process up to 3 paper links
                for i, link in enumerate(paper_links[:3]):
                    if ".pdf" in link:
                        # Download and process PDF
                        pdf_path = os.path.join(self.pdf_dir, f"{name.replace(' ', '_')}_{i}.pdf")
                        self.browser.download_pdf(link, pdf_path)
                        self._extract_emails_from_pdf(pdf_path, results)
                    else:
                        # Visit paper page
                        self.browser.navigate(link)
                        time.sleep(3)
                        
                        # Get page content
                        paper_content = self.browser.get_page_content()
                        if paper_content:
                            # Look for PDF links
                            soup = BeautifulSoup(paper_content.get("html", ""), "html.parser")
                            pdf_links = []
                            
                            for a_tag in soup.find_all("a", href=True):
                                href = a_tag.get("href", "")
                                if ".pdf" in href:
                                    pdf_links.append(href)
                            
                            # Download and process first PDF
                            if pdf_links:
                                pdf_url = pdf_links[0]
                                if not pdf_url.startswith("http"):
                                    if pdf_url.startswith("/"):
                                        pdf_url = f"https://scholar.google.com{pdf_url}"
                                    else:
                                        pdf_url = f"https://scholar.google.com/{pdf_url}"
                                
                                pdf_path = os.path.join(self.pdf_dir, f"{name.replace(' ', '_')}_{i}.pdf")
                                self.browser.download_pdf(pdf_url, pdf_path)
                                self._extract_emails_from_pdf(pdf_path, results)
            
            # Close browser session
            self.browser.close_session()
        
        except Exception as e:
            print(f"Error searching Google Scholar: {e}")
            # Ensure browser session is closed
            try:
                self.browser.close_session()
            except:
                pass
    
    def _search_general_web(self, name, affiliation, results):
        """
        Search for email on general web
        
        Args:
            name (str): Contributor name
            affiliation (str): Contributor affiliation
            results (dict): Results dictionary to update
        """
        try:
            # Format search query
            query = f"{name} email"
            if affiliation:
                query += f" {affiliation}"
            
            # Start browser session
            self.browser.start_session()
            
            # Navigate to Google
            self.browser.navigate("https://www.google.com/")
            time.sleep(2)
            
            # Get page content
            content = self.browser.get_page_content()
            
            # Find search input and submit search
            search_input_selector = "textarea[name='q']"
            self.browser.type(search_input_selector, query)
            time.sleep(1)
            
            # Press Enter to search
            search_button_selector = "input[name='btnK']"
            self.browser.click(search_button_selector)
            time.sleep(3)
            
            # Get search results
            content = self.browser.get_page_content()
            
            if content:
                # Parse content
                soup = BeautifulSoup(content.get("html", ""), "html.parser")
                
                # Extract text and look for email patterns
                text = soup.get_text()
                emails = re.findall(self.email_pattern, text)
                
                for email in emails:
                    if email not in results["potential_emails"] and self._is_valid_email(email):
                        results["potential_emails"].append(email)
                        results["sources"].append({
                            "email": email,
                            "source": "Google Search Results",
                            "url": "https://www.google.com/search?q=" + query.replace(" ", "+")
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
                        self.browser.navigate(link)
                        time.sleep(3)
                        
                        # Get page content
                        page_content = self.browser.get_page_content()
                        if page_content:
                            # Parse content
                            soup = BeautifulSoup(page_content.get("html", ""), "html.parser")
                            
                            # Extract text and look for email patterns
                            text = soup.get_text()
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
            
            # Close browser session
            self.browser.close_session()
        
        except Exception as e:
            print(f"Error searching general web: {e}")
            # Ensure browser session is closed
            try:
                self.browser.close_session()
            except:
                pass
    
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
