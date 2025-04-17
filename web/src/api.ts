import axios from 'axios';

// Define API base URL
const API_BASE_URL = 'http://localhost:8000';

// Define API endpoints
const API_ENDPOINTS = {
  extract: `${API_BASE_URL}/extract`,
  status: (repoPath: string) => `${API_BASE_URL}/status/${encodeURIComponent(repoPath)}`,
};

// Define API response types
export interface Contributor {
  name: string;
  email?: string;
  commit_count?: number;
  first_commit_date?: string;
  last_commit_date?: string;
}

export interface RepositoryResponse {
  repo_path: string;
  status: 'started' | 'in_progress' | 'completed' | 'error';
  message?: string;
  contributors?: Contributor[];
}

// API client functions
export const extractEmails = async (repoPath: string): Promise<RepositoryResponse> => {
  try {
    const response = await axios.post(API_ENDPOINTS.extract, { repo_path: repoPath });
    return response.data;
  } catch (error) {
    console.error('Error extracting emails:', error);
    throw error;
  }
};

export const getExtractionStatus = async (repoPath: string): Promise<RepositoryResponse> => {
  try {
    const response = await axios.get(API_ENDPOINTS.status(repoPath));
    return response.data;
  } catch (error) {
    console.error('Error getting extraction status:', error);
    throw error;
  }
};
