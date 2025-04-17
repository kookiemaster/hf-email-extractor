import React from "react";
import { useState, useEffect } from 'react';
import { extractEmails, getExtractionStatus, RepositoryResponse, Contributor } from './api';
import { Button } from './components/Button';
import { Input } from './components/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './components/Card';

const App: React.FC = () => {
  const [repoPath, setRepoPath] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RepositoryResponse | null>(null);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);

  // Function to handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!repoPath.trim()) {
      setError('Please enter a repository path');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Start extraction
      const response = await extractEmails(repoPath);
      setResult(response);
      
      // Start polling if extraction is not completed
      if (response.status !== 'completed' && response.status !== 'error') {
        startPolling();
      }
    } catch (err) {
      setError('Failed to start extraction. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Function to start polling for status updates
  const startPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
    }
    
    const interval = window.setInterval(async () => {
      if (!repoPath) return;
      
      try {
        const response = await getExtractionStatus(repoPath);
        setResult(response);
        
        // Stop polling if extraction is completed or failed
        if (response.status === 'completed' || response.status === 'error') {
          clearInterval(interval);
          setPollingInterval(null);
        }
      } catch (err) {
        console.error('Error polling for status:', err);
      }
    }, 5000); // Poll every 5 seconds
    
    setPollingInterval(interval);
  };

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            Hugging Face Contributor Email Extractor
          </h1>
          <p className="mt-3 text-xl text-gray-500 sm:mt-4">
            Extract contributor emails from Hugging Face repositories
          </p>
        </div>

        <Card className="mt-10">
          <CardHeader>
            <CardTitle>Enter Repository Path</CardTitle>
            <CardDescription>
              Provide the path to a Hugging Face repository (e.g., deepseek-ai/DeepSeek-V3-0324)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid w-full items-center gap-4">
                <div className="flex flex-col space-y-1.5">
                  <Input
                    id="repoPath"
                    placeholder="Enter repository path (e.g., deepseek-ai/DeepSeek-V3-0324)"
                    value={repoPath}
                    onChange={(e) => setRepoPath(e.target.value)}
                  />
                </div>
              </div>
              <Button 
                type="submit" 
                disabled={loading}
                className="w-full"
              >
                {loading ? 'Processing...' : 'Extract Emails'}
              </Button>
            </form>
          </CardContent>
        </Card>
          
        {error && (
          <Card variant="outline" className="mt-4 border-red-300 bg-red-50">
            <CardHeader>
              <CardTitle className="text-red-800 text-lg">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}
          
        {result && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Repository: {result.repo_path}</CardTitle>
              <CardDescription>
                Status: <span className={`font-medium ${result.status === 'completed' ? 'text-green-600' : result.status === 'error' ? 'text-red-600' : 'text-blue-600'}`}>{result.status}</span>
                {result.message && (
                  <span className="block mt-1">{result.message}</span>
                )}
              </CardDescription>
            </CardHeader>
                
            {result.contributors && result.contributors.length > 0 && (
              <CardContent>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Contributors
                </h3>
                <div className="space-y-4">
                  {result.contributors.map((contributor: Contributor, index: number) => (
                    <Card key={index} className="overflow-hidden">
                      <CardHeader className="bg-gray-50 py-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg text-indigo-600">
                            {contributor.name}
                          </CardTitle>
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            {contributor.commit_count || 0} commits
                          </span>
                        </div>
                      </CardHeader>
                      <CardContent className="py-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm font-medium text-gray-500">Email</p>
                            <p className="mt-1">{contributor.email || 'Not found'}</p>
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-500">First Commit</p>
                            <p className="mt-1">{contributor.first_commit_date || 'N/A'}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default App;
