import unittest
import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocess.image import canny_edge

class TestPreprocessing(unittest.TestCase):
    def setUp(self):
        # Create a test image
        self.test_dir = Path('tests/test_data')
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple test image (100x100 black square on white background)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255  # White background
        img[25:75, 25:75] = 0  # Black square
        
        self.test_image_path = self.test_dir / 'test_square.png'
        cv2.imwrite(str(self.test_image_path), img)
        
        # Read the image as bytes
        with open(self.test_image_path, 'rb') as f:
            self.test_image_bytes = f.read()

    def tearDown(self):
        # Clean up test files
        if self.test_image_path.exists():
            self.test_image_path.unlink()
        
        # Clean up any created edge maps
        for path in Path('temp_images').glob('edge_*_test_square.png'):
            path.unlink()

    def test_canny_edge_detection(self):
        # Test the canny_edge function
        edge_map_path = canny_edge(self.test_image_bytes, 'test_square.png')
        
        # Check that the file was created
        self.assertTrue(edge_map_path.exists())
        
        # Load the edge map and verify it has edges
        edge_map = cv2.imread(str(edge_map_path), cv2.IMREAD_GRAYSCALE)
        
        # The edge map should have some white pixels (edges)
        self.assertTrue(np.any(edge_map == 255))
        
        # Clean up
        edge_map_path.unlink()

    def test_canny_edge_invalid_image(self):
        # Test with invalid image bytes
        invalid_bytes = b'not an image'
        
        # Expect a ValueError
        with self.assertRaises(ValueError):
            canny_edge(invalid_bytes, 'invalid.png')

if __name__ == '__main__':
    unittest.main()