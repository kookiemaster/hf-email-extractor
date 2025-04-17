"""
README for Hugging Face Contributor Email Extractor
"""

# Hugging Face Contributor Email Extractor

A tool to extract contributor emails from Hugging Face repositories by first getting names from git logs and then finding emails through web searches, particularly from academic papers.

## Features

- Extract contributor names from Hugging Face repository git logs
- Search for contributor emails using Google Scholar and general web searches
- Download and parse PDFs to extract email addresses
- Prioritize academic emails over generic ones
- Modern web interface with React, Vite, Tailwind CSS, and shadcn UI
- FastAPI backend with background processing
- PostgreSQL database integration

## Architecture

The application consists of two main components:

1. **Server (FastAPI)**
   - RESTful API for repository processing
   - Background task processing for email extraction
   - Database integration for storing results
   - Comprehensive error handling and validation

2. **Web (React + Vite)**
   - Modern UI with Tailwind CSS and shadcn UI components
   - Real-time status updates with polling
   - Responsive design for all device sizes

## Installation

### Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL database

### Server Setup

1. Clone the repository
2. Install Python dependencies:
   ```
   cd server
   pip install requests beautifulsoup4 fastapi uvicorn psycopg2-binary anthropic openai pdf2image pytesseract PyPDF2
   ```
3. Configure environment variables in `server/config.py`
4. Start the server:
   ```
   cd server
   uvicorn backend:app --host 0.0.0.0 --port 8000
   ```

### Web Setup

1. Navigate to the web directory
2. Install Node.js dependencies:
   ```
   cd web
   npm install
   ```
3. Start the development server:
   ```
   npm run dev
   ```

## Usage

1. Enter a Hugging Face repository path (e.g., `deepseek-ai/DeepSeek-V3-0324`) in the web interface
2. Click "Extract Emails" to start the extraction process
3. The application will:
   - Clone the repository
   - Extract contributor names from git logs
   - Search for emails using Google Scholar and web searches
   - Download and parse PDFs to extract email addresses
   - Display the results in the web interface

## API Endpoints

- `POST /extract`: Start email extraction for a repository
- `GET /status/{repo_path}`: Get extraction status for a repository

## Database Schema

The application uses two tables:

1. `manus_hf_repositories`: Stores repository information
   - `id`: Primary key
   - `repo_path`: Repository path
   - `created_at`: Creation timestamp

2. `manus_hf_contributors`: Stores contributor information
   - `id`: Primary key
   - `repo_id`: Foreign key to repositories table
   - `name`: Contributor name
   - `email`: Contributor email
   - `commit_count`: Number of commits
   - `first_commit_date`: Date of first commit
   - `last_commit_date`: Date of last commit
   - `created_at`: Creation timestamp

## License

This project is licensed under the MIT License.
