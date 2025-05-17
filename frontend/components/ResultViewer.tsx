import { useState } from 'react';
import { Button } from './ui/Button';
import { API_URL } from '@/lib/utils';

interface ResultViewerProps {
  edgeImageUrl: string;
  stylizedImageUrl: string;
  jobId: string;
  onReset: () => void;
}

export function ResultViewer({
  edgeImageUrl,
  stylizedImageUrl,
  jobId,
  onReset,
}: ResultViewerProps) {
  const [sliderValue, setSliderValue] = useState(50);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSliderValue(Number(e.target.value));
  };

  const downloadZip = () => {
    window.location.href = `${API_URL}/download/${jobId}`;
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="mb-6 text-center">
        <h3 className="text-xl font-semibold mb-1">Your Stylized Image</h3>
        <p className="text-gray-600 text-sm">
          Slide to compare layers or download all files
        </p>
      </div>

      <div className="relative border rounded-lg overflow-hidden aspect-square">
        {/* Base layer (stylized image) */}
        <img
          src={stylizedImageUrl}
          alt="Stylized"
          className="absolute top-0 left-0 w-full h-full object-cover"
        />

        {/* Overlay layer (edge map) with clip-path determined by slider */}
        <div
          className="absolute top-0 left-0 w-full h-full"
          style={{
            clipPath: `inset(0 ${100 - sliderValue}% 0 0)`,
          }}
        >
          <img
            src={edgeImageUrl}
            alt="Edge Map"
            className="w-full h-full object-cover"
          />
        </div>

        {/* Slider divider line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-md"
          style={{ left: `${sliderValue}%` }}
        />

        {/* Slider handle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center cursor-pointer"
          style={{ left: `${sliderValue}%`, transform: 'translate(-50%, -50%)' }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-gray-600"
          >
            <path d="M16 8l-8 8m0-8l8 8" />
          </svg>
        </div>
      </div>

      <input
        type="range"
        min="0"
        max="100"
        value={sliderValue}
        onChange={handleSliderChange}
        className="w-full mt-4 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
      />

      <div className="flex justify-between mt-6 space-x-4">
        <Button variant="outline" onClick={onReset} className="flex-1">
          Start Over
        </Button>
        <Button onClick={downloadZip} className="flex-1">
          Download ZIP
        </Button>
      </div>
    </div>
  );
}