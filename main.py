import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import uvicorn

app = FastAPI(title="Whisper Transcription API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global model variable
model = None

def get_device_and_compute_type():
    """Determine the best device and compute type for the current system."""
    try:
        # Try to detect if we have a GPU available
        import torch
        if torch.cuda.is_available():
            return "cuda", "float16"
    except ImportError:
        pass

    # Fallback to CPU
    return "cpu", "int8"

@app.on_event("startup")
async def startup_event():
    """Initialize the Whisper model on startup."""
    global model

    # Get optimal device and compute type
    device, compute_type = get_device_and_compute_type()

    print(f"Initializing Whisper model with device: {device}, compute_type: {compute_type}")

    # Initialize with base model (good balance of speed/accuracy)
    # You can change to "small", "medium", "large-v2", or "large-v3" based on your needs
    model_size = os.getenv("WHISPER_MODEL_SIZE", "base")

    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        download_root=os.getenv("WHISPER_CACHE_DIR", None)
    )

    print(f"Whisper model '{model_size}' loaded successfully!")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Whisper Transcription API is running", "status": "healthy"}

@app.get("/health")
async def health():
    """Detailed health check."""
    global model
    return {
        "status": "healthy" if model is not None else "initializing",
        "model_loaded": model is not None
    }

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    output_language: str = Form("en")
):
    """
    Transcribe an audio file to text.

    Args:
        file: Audio file (wav, mp3, m4a, etc.)
        language: Optional input language code (e.g., 'en', 'sv'). If not provided, auto-detection is used.
        output_language: Output language code ('en', 'sv', 'es', etc.). Default: 'en' (English)
                        If different from detected language, translation is performed.

    Returns:
        JSON response with transcribed text and metadata
    """
    # Validate parameters FIRST (before any processing)
    supported_languages = {"en", "sv", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "nl", "pl", "tr"}

    if output_language not in supported_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported output language '{output_language}'. Supported: {', '.join(sorted(supported_languages))}")

    if language and language not in supported_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported input language '{language}'. Supported: {', '.join(sorted(supported_languages))}")

    # Check model availability
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    # Check file type
    if not file.content_type or not file.content_type.startswith(("audio/", "video/")):
        # Be more permissive and allow common file extensions
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.mp4', '.mov', '.avi'}
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "audio").suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Start timing
        start_time = time.time()

        # Determine task based on desired output language
        if output_language == "en":
            # Default to translate task (will transcribe if English, translate if other language)
            task = "translate"
            transcribe_language = language  # None for auto-detect, or specified language
        else:
            # For non-English output, transcribe in that language
            task = "transcribe"
            transcribe_language = language or output_language

        print(f"Task: {task}, Language: {transcribe_language or 'auto-detect'}, Output: {output_language}")

        # Single transcribe/translate pass
        segments, info = model.transcribe(
            tmp_file_path,
            language=transcribe_language,
            task=task,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        detected_language = info.language
        print(f"Detected language: {detected_language} (confidence: {info.language_probability:.3f})")

        # Collect all segments
        transcription_segments = []
        full_text = ""

        for segment in segments:
            segment_data = {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
                "confidence": round(segment.avg_logprob, 3) if hasattr(segment, 'avg_logprob') else None
            }
            transcription_segments.append(segment_data)
            full_text += segment.text.strip() + " "

        # Calculate processing time
        processing_time = time.time() - start_time

        # Clean up temporary file
        os.unlink(tmp_file_path)

        # Log processing stats
        print(f"Transcription completed in {processing_time:.2f}s for {info.duration:.2f}s audio (model: {os.getenv('WHISPER_MODEL_SIZE', 'base')})")

        # Prepare response
        response = {
            "text": full_text.strip(),
            "detected_language": detected_language,
            "output_language": output_language,
            "language_probability": round(info.language_probability, 3) if hasattr(info, 'language_probability') else None,
            "duration": round(info.duration, 2),
            "processing_time": round(processing_time, 2),
            "segments": transcription_segments,
            "task": task
        }

        return JSONResponse(content=response)

    except Exception as e:
        # Clean up temporary file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass

        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)