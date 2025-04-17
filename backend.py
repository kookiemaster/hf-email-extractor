"""
FastAPI backend for Hugging Face Contributor Email Extractor
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import os
import tempfile
import shutil
import json
import time
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from huggingface_scraper import HuggingFaceScraper
from git_log_parser import GitLogParser
from email_searcher import EmailSearcher
from validation import validate_repository_path, ValidationError, handle_api_error
from config import DB_CONNECTION_STRING, DB_TABLE_PREFIX

# Initialize FastAPI app
app = FastAPI(title="Hugging Face Contributor Email Extractor")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize components
hf_scraper = HuggingFaceScraper()
email_searcher = EmailSearcher()

# Define request and response models
class RepositoryRequest(BaseModel):
    repo_path: str
    
    @validator('repo_path')
    def validate_repo_path(cls, v):
        try:
            validate_repository_path(v)
            return v
        except ValidationError as e:
            raise ValueError(e.message)

class ContributorResponse(BaseModel):
    name: str
    email: Optional[str] = None
    commit_count: Optional[int] = None
    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None

class RepositoryResponse(BaseModel):
    repo_path: str
    status: str
    message: Optional[str] = None
    contributors: Optional[List[ContributorResponse]] = None

# Global variable to store extraction results
extraction_results = {}

# Database functions
def init_db():
    """Initialize database tables if they don't exist"""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Create repositories table
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE_PREFIX}repositories (
            id SERIAL PRIMARY KEY,
            repo_path VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create contributors table
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE_PREFIX}contributors (
            id SERIAL PRIMARY KEY,
            repo_id INTEGER REFERENCES {DB_TABLE_PREFIX}repositories(id),
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            commit_count INTEGER,
            first_commit_date VARCHAR(255),
            last_commit_date VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(repo_id, name)
        )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def save_to_db(repo_path, contributors):
    """Save extraction results to database"""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert repository
        cursor.execute(
            f"INSERT INTO {DB_TABLE_PREFIX}repositories (repo_path) VALUES (%s) ON CONFLICT (repo_path) DO UPDATE SET repo_path = %s RETURNING id",
            (repo_path, repo_path)
        )
        repo_id = cursor.fetchone()['id']
        
        # Insert contributors
        for contributor in contributors:
            cursor.execute(
                f"""
                INSERT INTO {DB_TABLE_PREFIX}contributors 
                (repo_id, name, email, commit_count, first_commit_date, last_commit_date) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (repo_id, name) 
                DO UPDATE SET 
                    email = %s,
                    commit_count = %s,
                    first_commit_date = %s,
                    last_commit_date = %s
                """,
                (
                    repo_id, 
                    contributor['name'], 
                    contributor.get('email', None),
                    contributor.get('commit_count', None),
                    contributor.get('first_commit_date', None),
                    contributor.get('last_commit_date', None),
                    contributor.get('email', None),
                    contributor.get('commit_count', None),
                    contributor.get('first_commit_date', None),
                    contributor.get('last_commit_date', None)
                )
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False

# Background task for extracting contributor emails
def extract_contributor_emails(repo_path: str):
    """
    Extract contributor emails from a Hugging Face repository
    
    Args:
        repo_path (str): Repository path (e.g., 'deepseek-ai/DeepSeek-V3-0324')
    """
    try:
        # Update status
        extraction_results[repo_path] = {
            "status": "in_progress",
            "message": "Extracting repository information...",
            "contributors": []
        }
        
        # Get repository info
        repo_info = hf_scraper.get_repository_info(repo_path)
        if not repo_info:
            extraction_results[repo_path] = {
                "status": "error",
                "message": f"Repository {repo_path} not found"
            }
            return
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        # Update status
        extraction_results[repo_path]["message"] = "Cloning repository..."
        
        # Clone repository
        clone_dir = hf_scraper.clone_repository(repo_path, temp_dir)
        if not clone_dir:
            extraction_results[repo_path] = {
                "status": "error",
                "message": f"Failed to clone repository {repo_path}"
            }
            shutil.rmtree(temp_dir)
            return
        
        # Update status
        extraction_results[repo_path]["message"] = "Extracting contributors from git logs..."
        
        # Extract contributors from git logs
        git_parser = GitLogParser(clone_dir)
        contributors = git_parser.extract_contributors()
        
        # Update status
        extraction_results[repo_path]["message"] = "Searching for contributor emails..."
        
        # Search for emails
        for i, contributor in enumerate(contributors):
            # Skip if email is already available and valid
            if contributor.get("email") and "@" in contributor.get("email"):
                extraction_results[repo_path]["contributors"].append(contributor)
                continue
            
            # Update status
            extraction_results[repo_path]["message"] = f"Searching for email of {contributor['name']} ({i+1}/{len(contributors)})..."
            
            # Search for email
            email_results = email_searcher.search_for_email(contributor["name"])
            
            # Update contributor with email
            if email_results["most_likely_email"]:
                contributor["email"] = email_results["most_likely_email"]
            
            # Add to results
            extraction_results[repo_path]["contributors"].append(contributor)
        
        # Update status
        extraction_results[repo_path]["status"] = "completed"
        extraction_results[repo_path]["message"] = "Extraction completed successfully"
        
        # Save to database
        try:
            save_to_db(repo_path, contributors)
        except Exception as e:
            print(f"Error saving to database: {e}")
        
        # Clean up
        shutil.rmtree(temp_dir)
    
    except Exception as e:
        extraction_results[repo_path] = {
            "status": "error",
            "message": f"Error extracting contributor emails: {str(e)}"
        }
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

# Exception handler for validation errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": exc.message}
    )

# Exception handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"An unexpected error occurred: {str(exc)}"}
    )

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hugging Face Contributor Email Extractor API"}

@app.post("/extract", response_model=RepositoryResponse)
async def extract_emails(repo_request: RepositoryRequest, background_tasks: BackgroundTasks):
    """
    Extract contributor emails from a Hugging Face repository
    
    Args:
        repo_request (RepositoryRequest): Repository request
    
    Returns:
        RepositoryResponse: Repository response
    """
    try:
        repo_path = repo_request.repo_path
        
        # Check if extraction is already in progress or completed
        if repo_path in extraction_results:
            return {
                "repo_path": repo_path,
                "status": extraction_results[repo_path]["status"],
                "message": extraction_results[repo_path]["message"],
                "contributors": extraction_results[repo_path].get("contributors", None)
            }
        
        # Start extraction in background
        background_tasks.add_task(extract_contributor_emails, repo_path)
        
        # Return initial response
        return {
            "repo_path": repo_path,
            "status": "started",
            "message": "Email extraction started"
        }
    except ValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": e.message}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
        )

@app.get("/status/{repo_path}", response_model=RepositoryResponse)
async def get_extraction_status(repo_path: str):
    """
    Get extraction status for a repository
    
    Args:
        repo_path (str): Repository path
    
    Returns:
        RepositoryResponse: Repository response
    """
    try:
        # Validate repository path
        validate_repository_path(repo_path)
        
        if repo_path not in extraction_results:
            raise HTTPException(status_code=404, detail=f"No extraction found for repository {repo_path}")
        
        return {
            "repo_path": repo_path,
            "status": extraction_results[repo_path]["status"],
            "message": extraction_results[repo_path]["message"],
            "contributors": extraction_results[repo_path].get("contributors", None)
        }
    except ValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": e.message}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
        )

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    # Initialize database
    init_db()

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
