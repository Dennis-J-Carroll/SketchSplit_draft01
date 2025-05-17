from PIL import Image, ImageDraw, ImageFont
import imageio
from pathlib import Path
import zipfile
import json
import os

TEMP_STORAGE_BASE = Path("temp_images") # Should match app.py

def ensure_rgba_and_transparent_background(image_path: Path, primary_color=(0,0,0), background_color_value=255) -> Image.Image:
    """Converts image (e.g. Canny edge map) to RGBA with transparent background."""
    img = Image.open(image_path).convert("L") # Grayscale
    rgba_img = Image.new("RGBA", img.size)
    
    pixels = img.load()
    rgba_pixels = rgba_img.load()

    for y in range(img.height):
        for x in range(img.width):
            if pixels[x, y] == background_color_value: # e.g., white for Canny
                rgba_pixels[x, y] = (0, 0, 0, 0)  # Transparent
            else: # Lines or other features
                rgba_pixels[x, y] = primary_color + (255,) # Opaque primary color (e.g., black)
    return rgba_img

def merge_layers(base_image_path: Path, overlay_image_path: Path, output_path: Path):
    """
    Merges two images. Assumes base_image_path is the stylized image from Replicate
    and overlay_image_path is the Canny edge map (which will be made transparent).
    """
    stylized_img = Image.open(base_image_path).convert("RGBA")
    
    # Make Canny edge map (overlay) have transparent background and black lines
    edge_map_rgba = ensure_rgba_and_transparent_background(overlay_image_path, primary_color=(0,0,0))

    # Composite: overlay edge map on top of stylized image
    composite_img = Image.alpha_composite(stylized_img, edge_map_rgba)
    composite_img.save(output_path)
    return output_path

def create_gif_preview(layer_paths: list[Path], output_gif_path: Path, duration_ms: int = 400):
    """Creates a GIF from a list of layer image paths."""
    # Ensure imageio-ffmpeg is available if not using standard GIF features or for better compatibility
    # pip install imageio[ffmpeg] or imageio-ffmpeg
    frames = []
    for p_str in layer_paths:
        p = Path(p_str) # Ensure it's a Path object
        if p.exists():
            frames.append(imageio.v3.imread(p)) # imageio.v3.imread is preferred
        else:
            print(f"Warning: Frame not found at {p} for GIF creation.")
    
    if not frames:
        print("Error: No frames found for GIF creation.")
        # Create a dummy placeholder GIF or raise error
        # For now, let's create a small dummy frame if no real frames
        dummy_frame = Image.new("RGB", (100,100), "gray")
        draw = ImageDraw.Draw(dummy_frame)
        try:
            font = ImageFont.truetype("arial.ttf", 10) # Try to load a common font
        except IOError:
            font = ImageFont.load_default()
        draw.text((10,10), "No Frames", font=font, fill="red")
        frames.append(imageio.v3.imread(dummy_frame))


    imageio.v3.mimsave(output_gif_path, frames, duration=duration_ms, loop=0) # loop=0 for infinite loop
    return output_gif_path

def create_zip_bundle(job_id: str, files_to_zip: dict[str, Path], output_zip_path: Path) -> Path:
    """
    Creates a ZIP file containing specified layers and previews.
    files_to_zip is a dictionary like {"edges.png": Path(...), "stylized.png": Path(...), "preview.gif": Path(...)}
    """
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname, file_path in files_to_zip.items():
            if file_path.exists():
                zf.write(file_path, arcname=arcname)
            else:
                print(f"Warning: File {file_path} not found for zipping. Skipping.")
        
        # Add steps.json
        steps_data = {
            "job_id": job_id,
            "message": "SketchSplit layers and preview.",
            "files_included": list(files_to_zip.keys())
        }
        zf.writestr("steps.json", json.dumps(steps_data, indent=2))
        
    return output_zip_path

# Optional MP4 generation (2.5.3)
def create_mp4_preview(frame_pattern: str, output_mp4_path: Path, fps: int = 5):
    """
    Creates an MP4 from frames using ffmpeg.
    frame_pattern: e.g., "temp_images/job_xyz_frame-%d.png"
    Requires ffmpeg to be installed and in PATH.
    """
    # This is a system call. Ensure security if paths/args are from user input.
    # For controlled frame_pattern, it's safer.
    command = [
        "ffmpeg",
        "-y", # Overwrite output files without asking
        "-r", str(fps),
        "-i", frame_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_mp4_path)
    ]
    try:
        import subprocess
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        print("FFmpeg output:", process.stdout)
        return output_mp4_path
    except FileNotFoundError:
        print("Error: ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print("Error during ffmpeg execution:")
        print("FFmpeg stderr:", e.stderr)
        return None