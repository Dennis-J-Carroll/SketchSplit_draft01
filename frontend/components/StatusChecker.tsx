import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { Button } from './ui/Button';

interface StatusCheckerProps {
  jobId: string;
  onComplete: (edges: string, stylized: string, jobId: string) => void;
  edgePath: string;
}

interface JobStatus {
  job_id: string;
  status: string;
  edge_map_path: string | null;
  stylized_image_path: string | null;
  error_message: string | null;
}

export function StatusChecker({ jobId, onComplete, edgePath }: StatusCheckerProps) {
  const [status, setStatus] = useState<string>('processing');
  const [error, setError] = useState<string | null>(null);
  const [stylizedPath, setStylizedPath] = useState<string | null>(null);
  
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/status/${jobId}`);
        
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data: JobStatus = await response.json();
        setStatus(data.status);
        
        if (data.error_message) {
          setError(data.error_message);
        }
        
        if (data.stylized_image_path) {
          setStylizedPath(data.stylized_image_path);
        }
        
        if (data.status === 'complete' && data.edge_map_path && data.stylized_image_path) {
          onComplete(
            `${API_URL}/${data.edge_map_path}`, 
            `${API_URL}/${data.stylized_image_path}`,
            data.job_id
          );
          clearInterval(interval);
        }
        
        if (data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error checking status:', err);
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      }
    };
    
    // Initial check
    checkStatus();
    
    // Set up polling every 2 seconds
    interval = setInterval(checkStatus, 2000);
    
    return () => {
      clearInterval(interval);
    };
  }, [jobId, onComplete]);
  
  const downloadResults = () => {
    window.location.href = `${API_URL}/download/${jobId}`;
  };
  
  const statusMessages = {
    processing_upload: 'Uploading your image...',
    processing_canny: 'Extracting edges from your image...',
    processing_replicate: 'AI is stylizing your image (this may take 10-15 seconds)...',
    complete: 'Processing complete!',
    failed: 'Processing failed. Please try again.',
  };
  
  const statusMessage = statusMessages[status as keyof typeof statusMessages] || 'Processing your image...';
  
  return (
    <div className="w-full max-w-md mx-auto text-center">
      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-2">
          {status === 'complete' ? '✅ Complete!' : 'Processing Your Image'}
        </h3>
        
        <p className="text-gray-600 mb-4">{statusMessage}</p>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-4">
            {error}
          </div>
        )}
        
        {status !== 'complete' && status !== 'failed' && (
          <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="absolute top-0 left-0 h-full w-full bg-blue-500 rounded-full animate-pulse"></div>
          </div>
        )}
      </div>
      
      <div className="flex flex-col space-y-4">
        {/* Edge map preview */}
        {edgePath && (
          <div className="border rounded-lg p-2">
            <p className="text-sm font-medium text-gray-700 mb-2">Edge Map</p>
            <img 
              src={`${API_URL}/${edgePath}`} 
              alt="Edge Map" 
              className="w-full h-auto rounded"
            />
          </div>
        )}
        
        {/* Stylized image preview (when available) */}
        {stylizedPath && (
          <div className="border rounded-lg p-2">
            <p className="text-sm font-medium text-gray-700 mb-2">Stylized Image</p>
            <img 
              src={`${API_URL}/${stylizedPath}`} 
              alt="Stylized" 
              className="w-full h-auto rounded"
            />
          </div>
        )}
      </div>
      
      {status === 'complete' && (
        <Button 
          onClick={downloadResults}
          className="mt-4 w-full"
        >
          Download All Layers (ZIP)
        </Button>
      )}
    </div>
  );
}