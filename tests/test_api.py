import unittest
import os
import sys
from fastapi.testclient import TestClient
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # Create test image directory
        self.test_dir = Path('tests/test_data')
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to a test image (should be created in test_preprocess.py)
        self.test_image_path = self.test_dir / 'test_square.png'
        
        # Skip tests if the test image doesn't exist
        if not self.test_image_path.exists():
            self.skipTest("Test image not found")

    def test_health_endpoint(self):
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_stylize_endpoint_file_validation(self):
        # Test with invalid file type
        with open(__file__, 'rb') as f:
            response = self.client.post(
                "/stylize",
                files={"file": ("test.py", f, "text/x-python")}
            )
        
        self.assertEqual(response.status_code, 415)
        self.assertIn("Unsupported file type", response.json()["detail"])

    def test_stylize_endpoint(self):
        # Only run this if the test image exists
        if not self.test_image_path.exists():
            self.skipTest("Test image not found")
            
        with open(self.test_image_path, 'rb') as f:
            response = self.client.post(
                "/stylize",
                files={"file": ("test_square.png", f, "image/png")},
                data={"prompt": "test prompt"}
            )
        
        # Test should still pass even if Replicate isn't configured
        self.assertEqual(response.status_code, 200)
        
        # Response should include a job_id and edge_path
        data = response.json()
        self.assertIn("job_id", data)
        self.assertIn("edge_path", data)

if __name__ == '__main__':
    unittest.main()