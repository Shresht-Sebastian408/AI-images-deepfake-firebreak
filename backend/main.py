from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
import os

# Import the ML Pipeline
from ml_pipeline import process_and_predict

app = FastAPI(
    title="Deepfake Firebreak Bridge API", 
    description="Bridge between the Chrome Extension and the Vertex AI Pipeline"
)

# Enable CORS so the Chrome Extension can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to your extension's ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MediaRequest(BaseModel):
    url: str
    mediaType: str

class DetectionResponse(BaseModel):
    isAIGenerated: bool
    confidence: float
    type: str

@app.post("/analyze", response_model=DetectionResponse)
async def analyze_media(request: MediaRequest):
    """
    Downloads the media from the URL provided by the Chrome extension,
    runs the 2D FFT spectral artifact extraction, and performs inference
    using the Spectral CNN model.
    """
    print(f"\n--- Analyzing New Media ---")
    print(f"Type: {request.mediaType}")
    print(f"URL: {request.url[:100]}...")
    
    # We currently only support images for the live FFT extraction in this mock.
    # Video extraction would require extracting a frame first.
    if request.mediaType != "image":
        print("Skipping non-image media for local mock.")
        return DetectionResponse(isAIGenerated=False, confidence=0.0, type=request.mediaType)
    
    try:
        # 1. Download the image
        print("Downloading image...")
        # Added headers to avoid 403 Forbidden on some CDNs like Wikimedia/Reddit
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(request.url, headers=headers, timeout=5)
        resp.raise_for_status()
        image_bytes = resp.content
        print(f"Download complete. Size: {len(image_bytes)} bytes")
        
        # 2. Run the Deepfake Firebreak ML Pipeline!
        print("Running 2D FFT Preprocessing and CNN Inference...")
        start_time = time.time()
        
        confidence = process_and_predict(image_bytes)
        
        elapsed = time.time() - start_time
        print(f"Inference complete in {elapsed:.2f} seconds.")
        print(f"Raw CNN output (confidence): {confidence:.4f}")
        
        # 3. Determine threshold (randomized threshold since model is untrained for demo purposes)
        # In production, use a fixed threshold like 0.5
        is_ai = confidence > 0.5
        
        return DetectionResponse(
            isAIGenerated=is_ai,
            confidence=confidence,
            type=request.mediaType
        )
        
    except Exception as e:
        print(f"Error analyzing media: {e}")
        # Return a safe default so the extension doesn't crash
        return DetectionResponse(
            isAIGenerated=False,
            confidence=0.0,
            type=request.mediaType
        )

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
