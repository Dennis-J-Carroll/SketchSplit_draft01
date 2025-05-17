from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid
import os
import shutil
import httpx  # For downloading Replicate image
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Local modules
from .preprocess import canny_edge
from . import replicate_client
from . import composer

# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not API_TOKEN:
    print("WARNING: REPLICATE_API_TOKEN is not set. Replicate integration will fail.")

# Initialize FastAPI app
app = FastAPI()

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Local Next.js dev server
    "https://sketchsplit.vercel.app",  # Production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # If you need to handle cookies or auth headers
    allow_methods=["*"],     # Or specify ["GET", "POST"]
    allow_headers=["*"],     # Or specify necessary headers
)

# --- Configuration ---
# File-type & size validation
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/heic"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Temporary storage for uploaded/processed files
TEMP_IMAGE_DIR = Path("temp_images")
TEMP_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store for job status and file paths
JOBS_DATA = {} 

# --- Models ---
class StylizeResponse(BaseModel):
    job_id: uuid.UUID
    edge_path: str  # Relative path or identifier for the edge map
    stylized_url: Optional[str] = None  # Will be populated by Replicate integration

class StylizeInitiateResponse(BaseModel):
    job_id: str
    edge_path: str  # Relative path for frontend to show optimistic preview

class HealthResponse(BaseModel):
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    edge_map_path: Optional[str] = None  # Relative path
    stylized_image_path: Optional[str] = None  # Relative path (once available)
    error_message: Optional[str] = None
    # Add other paths if frontend needs them before full download

# --- Background Tasks ---
async def process_stylization_in_background(job_id: str, edge_map_abs_path: str, prompt: str):
    JOBS_DATA[job_id]["status"] = "processing_replicate"
    try:
        # 1. Call Replicate
        stylized_url = replicate_client.stylize_image_with_replicate(
            edge_map_path=str(edge_map_abs_path),  # replicate_client expects string path
            prompt=prompt
        )
        if not stylized_url:
            raise ValueError("Replicate did not return a URL.")

        # 2. Download the stylized image from Replicate URL
        job_temp_dir = TEMP_IMAGE_DIR / job_id
        job_temp_dir.mkdir(parents=True, exist_ok=True)
        stylized_image_filename = f"stylized_{Path(JOBS_DATA[job_id]['original_filename']).stem}.png"
        stylized_image_path = job_temp_dir / stylized_image_filename

        async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout for download
            response = await client.get(stylized_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            with open(stylized_image_path, 'wb') as f:
                f.write(response.content)
        
        JOBS_DATA[job_id]["stylized_image_path"] = stylized_image_path
        JOBS_DATA[job_id]["status"] = "complete"  # Mark as complete for polling
        print(f"Job {job_id} stylization complete. Image at {stylized_image_path}")

    except Exception as e:
        print(f"Error in background stylization for job {job_id}: {e}")
        JOBS_DATA[job_id]["status"] = "failed"
        JOBS_DATA[job_id]["error_message"] = str(e)

# --- Routes ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}

@app.post("/stylize", response_model=StylizeInitiateResponse)
@limiter.limit("60/minute")
async def create_stylize_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("pencil sketch")
):
    # File-type validation
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415, detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    # Size validation
    contents = await file.read()
    actual_size = len(contents)  # Get size from read content

    if actual_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413, detail=f"File too large: {actual_size / (1024*1024):.2f} MB. Maximum size is {MAX_FILE_SIZE_MB} MB."
        )

    job_id = str(uuid.uuid4())
    JOBS_DATA[job_id] = {"status": "processing_upload", "original_filename": file.filename}

    job_temp_dir = TEMP_IMAGE_DIR / job_id
    job_temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        JOBS_DATA[job_id]["status"] = "processing_canny"
        edge_map_path_obj = canny_edge(contents, file.filename)  # This saves to global TEMP_IMAGE_DIR
        
        # Move edge_map to job-specific folder and update path
        final_edge_map_name = f"edge_{Path(file.filename).stem}.png"
        final_edge_map_path = job_temp_dir / final_edge_map_name
        shutil.move(edge_map_path_obj, final_edge_map_path)  # Move from global temp to job specific temp
        
        JOBS_DATA[job_id]["edge_map_path"] = final_edge_map_path

    except Exception as e:
        JOBS_DATA[job_id]["status"] = "failed"
        JOBS_DATA[job_id]["error_message"] = f"Preprocessing error: {e}"
        raise HTTPException(status_code=500, detail=JOBS_DATA[job_id]["error_message"])

    # Kick off Replicate processing in the background
    final_prompt = prompt if prompt else "a beautiful sketch"
    background_tasks.add_task(
        process_stylization_in_background,
        job_id,
        str(final_edge_map_path.resolve()),  # Pass absolute path to background task
        final_prompt
    )
    
    # Return job_id and edge_map_path for optimistic UI
    relative_edge_path = str(final_edge_map_path.relative_to(Path.cwd()))
    
    return StylizeInitiateResponse(
        job_id=job_id,
        edge_path=relative_edge_path 
    )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job_info = JOBS_DATA.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Make paths relative for the response
    edge_path_rel = None
    if job_info.get("edge_map_path"):
        edge_path_rel = str(Path(job_info["edge_map_path"]).relative_to(Path.cwd()))
    
    stylized_path_rel = None
    if job_info.get("stylized_image_path"):
        stylized_path_rel = str(Path(job_info["stylized_image_path"]).relative_to(Path.cwd()))

    return JobStatusResponse(
        job_id=job_id,
        status=job_info["status"],
        edge_map_path=edge_path_rel,
        stylized_image_path=stylized_path_rel,
        error_message=job_info.get("error_message")
    )

@app.get("/download/{job_id}")
async def download_results(job_id: str):
    job_info = JOBS_DATA.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    if job_info["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not yet complete. Status: {job_info['status']}")

    edge_map_path = job_info.get("edge_map_path")
    stylized_image_path = job_info.get("stylized_image_path")

    if not edge_map_path or not Path(edge_map_path).exists() or \
       not stylized_image_path or not Path(stylized_image_path).exists():
        raise HTTPException(status_code=500, detail="Required image files for job are missing.")

    job_temp_dir = TEMP_IMAGE_DIR / job_id  # Base directory for this job's files

    # Define paths for composed files
    composite_image_path = job_temp_dir / f"composite_{Path(job_info['original_filename']).stem}.png"
    gif_preview_path = job_temp_dir / f"preview_{Path(job_info['original_filename']).stem}.gif"
    zip_bundle_path = job_temp_dir / f"sketchsplit_{job_id}.zip"

    # 1. Merge PNG layers (stylized image as base, edge map as overlay)
    try:
        composer.merge_layers(stylized_image_path, edge_map_path, composite_image_path)
        JOBS_DATA[job_id]["composite_image_path"] = composite_image_path
    except Exception as e:
        print(f"Error merging layers for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error merging image layers: {e}")

    # 2. Generate GIF preview (e.g., from edge map, stylized, and composite)
    # Ensure these paths are absolute if imageio needs them
    frames_for_gif = [
        Path(edge_map_path).resolve(), 
        Path(stylized_image_path).resolve(),
        Path(composite_image_path).resolve()
    ]
    try:
        composer.create_gif_preview(frames_for_gif, gif_preview_path)
        JOBS_DATA[job_id]["gif_preview_path"] = gif_preview_path
    except Exception as e:
        print(f"Error creating GIF for job {job_id}: {e}")
        # Continue to ZIP creation, GIF is optional for download
        pass  # Or raise HTTPException if GIF is critical

    # 3. Create ZIP bundle
    files_to_bundle = {
        f"01_edge_map_{Path(job_info['original_filename']).stem}.png": Path(edge_map_path),
        f"02_stylized_{Path(job_info['original_filename']).stem}.png": Path(stylized_image_path),
        f"03_composite_{Path(job_info['original_filename']).stem}.png": Path(composite_image_path),
    }
    if Path(gif_preview_path).exists():  # Only add GIF if created successfully
         files_to_bundle[f"preview_{Path(job_info['original_filename']).stem}.gif"] = Path(gif_preview_path)
    
    try:
        composer.create_zip_bundle(job_id, files_to_bundle, zip_bundle_path)
        JOBS_DATA[job_id]["zip_bundle_path"] = zip_bundle_path
    except Exception as e:
        print(f"Error creating ZIP for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP bundle: {e}")
        
    return FileResponse(
        path=zip_bundle_path,
        filename=f"sketchsplit_results_{job_id}.zip",
        media_type='application/zip'
    )

# Add a static route to serve processed images for optimistic UI
if not Path(TEMP_IMAGE_DIR).is_absolute():  # Ensure it's discoverable
    app.mount(f"/{TEMP_IMAGE_DIR.name}", StaticFiles(directory=TEMP_IMAGE_DIR), name="temp_images_static")
else:
    print(f"Warning: TEMP_IMAGE_DIR {TEMP_IMAGE_DIR} is absolute. Static file serving needs review.")