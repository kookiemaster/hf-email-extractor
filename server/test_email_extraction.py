"""
Main script to integrate the fixed components and test email extraction
"""
import os
import sys
import tempfile
import json

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.fixed_huggingface_scraper import FixedHuggingFaceScraper
from server.alternative_email_searcher import AlternativeEmailSearcher
from server.direct_contributor_extractor import DirectContributorExtractor

def extract_contributor_emails(repo_path):
    """
    Extract contributor emails from a Hugging Face repository
    
    Args:
        repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
        
    Returns:
        dict: Results including contributors and their emails
    """
    print(f"Extracting contributor emails from {repo_path}...")
    
    # Initialize components
    scraper = FixedHuggingFaceScraper()
    email_searcher = AlternativeEmailSearcher()
    contributor_extractor = DirectContributorExtractor()
    
    # Get repository info
    repo_info = scraper.get_repository_info(repo_path)
    if not repo_info:
        return {"status": "error", "message": f"Repository {repo_path} not found"}
    
    print(f"Repository info: {repo_info}")
    
    # Get contributors - try direct extraction first, then fallback to git commits
    contributors = contributor_extractor.get_contributors(repo_path)
    if not contributors:
        contributors = scraper.get_contributors(repo_path)
    
    if not contributors:
        return {"status": "error", "message": f"No contributors found for repository {repo_path}"}
    
    print(f"Found {len(contributors)} contributors")
    
    # Search for emails
    results = {
        "repo_path": repo_path,
        "status": "completed",
        "message": "Email extraction completed",
        "contributors": []
    }
    
    for contributor in contributors:
        print(f"Searching for email for {contributor['name']}...")
        
        # Extract affiliation from repository owner
        affiliation = repo_info["owner"]
        
        # Search for email
        email_results = email_searcher.search_for_email(contributor["name"], affiliation)
        
        # Add email to contributor info
        contributor_with_email = {
            "name": contributor["name"],
            "email": email_results.get("most_likely_email"),
            "commit_count": contributor.get("commit_count"),
            "first_commit_date": contributor.get("first_commit_date"),
            "last_commit_date": contributor.get("last_commit_date"),
            "potential_emails": email_results.get("potential_emails", []),
            "email_sources": email_results.get("sources", [])
        }
        
        results["contributors"].append(contributor_with_email)
        
        print(f"Email for {contributor['name']}: {contributor_with_email['email']}")
    
    return results

if __name__ == "__main__":
    # Check if repository path is provided as command line argument
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        # Default test case
        repo_path = "deepseek-ai/DeepSeek-V3-0324"
    
    # Extract contributor emails
    results = extract_contributor_emails(repo_path)
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Save results to file
    with open(f"{repo_path.replace('/', '_')}_emails.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {repo_path.replace('/', '_')}_emails.json")
