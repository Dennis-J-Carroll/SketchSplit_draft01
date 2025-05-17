import cv2
import numpy as np
from pathlib import Path
import uuid
import os # For saving to a temporary directory

# Ensure a temporary directory for processed images exists
TEMP_IMAGE_DIR = Path("temp_images")
TEMP_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

def canny_edge(image_bytes: bytes, filename: str) -> Path:
    """
    Applies Gaussian blur and Canny edge detection to an image.
    Saves the processed image to a temporary file and returns its path.

    Args:
        image_bytes: Raw bytes of the image.
        filename: Original filename, used to derive a unique name for the processed image.

    Returns:
        Path to the saved edge map image.
    """
    # Decode image bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image from bytes.")

    # 1.3.1 Noise reduction first (Gaussian Blur)
    # OpenCV tutorial suggests blurring before edge detection for better results.
    # Parameters: (image, kernel_size, sigmaX)
    # 5x5 kernel as specified in plan section 3.1
    blur = cv2.GaussianBlur(img, (5, 5), 0)

    # Convert to grayscale for Canny
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)

    # 1.3.1 Canny edge detection
    # Parameters: (image, threshold1, threshold2)
    # 100/200 are doc-recommended defaults as per plan section 3.1
    edges = cv2.Canny(gray, 100, 200)

    # Save the processed image
    # Create a unique filename for the edge map
    unique_id = uuid.uuid4()
    edge_map_filename = f"edge_{unique_id}_{Path(filename).stem}.png"
    edge_map_path = TEMP_IMAGE_DIR / edge_map_filename
    
    cv2.imwrite(str(edge_map_path), edges)
    
    return edge_map_path

# 1.3.2 Extra filters (stretch goal) - Placeholder
def adaptive_threshold_silhouette(image_bytes: bytes, filename: str) -> Path:
    """
    Applies adaptive thresholding to create a silhouette.
    (Placeholder for stretch goal)
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image from bytes.")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Example: cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # This is a placeholder; actual implementation would require tuning and saving.
    print("Adaptive thresholding not yet implemented.")
    
    # For now, returning a dummy path or raising NotImplementedError would be appropriate
    # For demonstration, let's assume it saves similarly if implemented
    dummy_path = TEMP_IMAGE_DIR / f"silhouette_{uuid.uuid4()}_{Path(filename).stem}.png"
    # cv2.imwrite(str(dummy_path), some_processed_image) 
    return dummy_path