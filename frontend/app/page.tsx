'use client';

import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { StatusChecker } from '@/components/StatusChecker';
import { ResultViewer } from '@/components/ResultViewer';
import { API_URL } from '@/lib/utils';

enum AppState {
  UPLOAD,
  PROCESSING,
  RESULT,
}

export default function Home() {
  const [appState, setAppState] = useState<AppState>(AppState.UPLOAD);
  const [isUploading, setIsUploading] = useState(false);
  const [jobId, setJobId] = useState<string>('');
  const [edgePath, setEdgePath] = useState<string>('');
  const [resultData, setResultData] = useState<{
    edgeUrl: string;
    stylizedUrl: string;
    jobId: string;
  } | null>(null);

  const handleUpload = async (file: File, prompt: string) => {
    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('prompt', prompt);
      
      const response = await fetch(`${API_URL}/stylize`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Store the job ID and edge path for status checking
      setJobId(data.job_id);
      setEdgePath(data.edge_path);
      
      // Move to processing state
      setAppState(AppState.PROCESSING);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcessingComplete = (
    edgeUrl: string,
    stylizedUrl: string,
    completedJobId: string
  ) => {
    setResultData({
      edgeUrl,
      stylizedUrl,
      jobId: completedJobId,
    });
    setAppState(AppState.RESULT);
  };

  const resetApp = () => {
    setAppState(AppState.UPLOAD);
    setJobId('');
    setEdgePath('');
    setResultData(null);
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <section className="mb-12 text-center">
        <h1 className="text-4xl font-bold mb-4">Transform Photos into Multi-Layer Sketches</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Upload an image and our AI will generate a stylized sketch with separate edge and fill layers
        </p>
      </section>

      <section className="bg-white rounded-xl shadow-lg p-6 mb-8">
        {appState === AppState.UPLOAD && (
          <FileUpload onUpload={handleUpload} isUploading={isUploading} />
        )}

        {appState === AppState.PROCESSING && jobId && (
          <StatusChecker 
            jobId={jobId} 
            onComplete={handleProcessingComplete}
            edgePath={edgePath}
          />
        )}

        {appState === AppState.RESULT && resultData && (
          <ResultViewer
            edgeImageUrl={resultData.edgeUrl}
            stylizedImageUrl={resultData.stylizedUrl}
            jobId={resultData.jobId}
            onReset={resetApp}
          />
        )}
      </section>

      <section className="text-center">
        <h2 className="text-2xl font-semibold mb-4">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="bg-blue-100 w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center">
              <span className="text-blue-600 text-2xl font-bold">1</span>
            </div>
            <h3 className="text-lg font-medium mb-2">Upload</h3>
            <p className="text-gray-600">Upload any photo (JPEG, PNG, HEIC) up to 10MB</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="bg-blue-100 w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center">
              <span className="text-blue-600 text-2xl font-bold">2</span>
            </div>
            <h3 className="text-lg font-medium mb-2">Process</h3>
            <p className="text-gray-600">AI extracts the edges and generates a stylized version</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="bg-blue-100 w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center">
              <span className="text-blue-600 text-2xl font-bold">3</span>
            </div>
            <h3 className="text-lg font-medium mb-2">Download</h3>
            <p className="text-gray-600">Get all layers as a ZIP bundle with edge map, stylized, and composite</p>
          </div>
        </div>
      </section>
    </div>
  );
}