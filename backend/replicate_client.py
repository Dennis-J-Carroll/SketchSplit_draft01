import replicate
import os
from dotenv import load_dotenv # Good practice to load here too if run independently or for clarity

# Load environment variables specifically for this client if needed,
# though app.py loading should make them available globally if this is imported.
load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_TOKEN:
    print("WARNING: REPLICATE_API_TOKEN not found in environment for replicate_client.py. Calls will fail.")
    # For a library, it's often better to let the calling code handle the missing token
    # or for Replicate client to raise its own error if token is not configured.
    # replicate.Client() will typically raise an error if the token isn't found.

# The Replicate client will automatically use REPLICATE_API_TOKEN from the environment.
# client = replicate.Client(api_token=REPLICATE_API_TOKEN) # Or explicitly pass if preferred

DEFAULT_MODEL_ID = "jagilley/controlnet-canny" # As per plan

def stylize_image_with_replicate(edge_map_path: str, prompt: str = "pencil sketch", model_id: str = None) -> str:
    """
    Sends an edge map image to Replicate for stylization using ControlNet.

    Args:
        edge_map_path: Path to the edge map image file.
        prompt: The prompt to guide the stylization.
        model_id: The Replicate model ID to use. Defaults to MODEL_ID from .env or DEFAULT_MODEL_ID.

    Returns:
        The URL of the stylized image from Replicate.
    
    Raises:
        replicate.exceptions.ReplicateError: If the API call fails.
        FileNotFoundError: If the edge_map_path does not exist.
    """
    if not os.path.exists(edge_map_path):
        raise FileNotFoundError(f"Edge map file not found at: {edge_map_path}")

    resolved_model_id = model_id or os.getenv("MODEL_ID", DEFAULT_MODEL_ID)
    
    print(f"Using Replicate model: {resolved_model_id}")
    print(f"Prompt: {prompt}")
    print(f"Edge map path: {edge_map_path}")

    try:
        with open(edge_map_path, "rb") as f:
            # The replicate.run() function handles client instantiation if not already done.
            # It expects a file-like object for image inputs.
            output = replicate.run(
                resolved_model_id,
                input={"image": f, "prompt": prompt}
                # Add other model-specific parameters if needed, e.g., "num_inference_steps", "guidance_scale"
                # "image_resolution" might also be relevant depending on the ControlNet model.
            )
        
        # The output structure can vary by model. 
        # For jagilley/controlnet, it's typically a list of URLs. We take the first.
        if isinstance(output, list) and len(output) > 0:
            stylized_url = output[0]
            print(f"Replicate output URL: {stylized_url}")
            return stylized_url
        else:
            # Log the unexpected output for debugging
            print(f"Unexpected output format from Replicate: {output}")
            raise ValueError("Unexpected output format from Replicate model. Expected a list of URLs.")

    except replicate.exceptions.ReplicateError as e:
        print(f"Replicate API error: {e}")
        raise  # Re-raise the exception to be handled by the caller
    except Exception as e:
        print(f"An unexpected error occurred in stylize_image_with_replicate: {e}")
        raise

# Example usage (for testing this module directly):
if __name__ == "__main__":
    # This requires a REPLICATE_API_TOKEN in your .env or environment
    # and a dummy edge map file.
    print("Running replicate_client.py example...")
    if not REPLICATE_API_TOKEN:
        print("REPLICATE_API_TOKEN not set. Cannot run example.")
    else:
        # Create a dummy edge map for testing
        dummy_edge_file = "dummy_edge_map.png"
        # You'd need a real image or a placeholder that replicate might process
        # For this example, let's assume a small black square png if you want to test it
        # For now, just a placeholder path
        if not os.path.exists(dummy_edge_file):
            print(f"Warning: Dummy file {dummy_edge_file} not found. Create one to test.")
        else:
            try:
                test_prompt = "A beautiful landscape painting"
                url = stylize_image_with_replicate(dummy_edge_file, prompt=test_prompt)
                print(f"Test - Stylized image URL: {url}")
            except FileNotFoundError as e:
                print(e)
            except replicate.exceptions.ReplicateError as e:
                print(f"Test - Replicate API Error: {e}")
            except Exception as e:
                print(f"Test - An unexpected error occurred: {e}")