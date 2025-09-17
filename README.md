# Whisper AI Transcription Service

A local FastAPI service for audio transcription using OpenAI's Whisper with the faster-whisper backend (CTranslate2) for improved performance.

## Features

- 🎵 Transcribe audio files to text
- 🌍 Support for multiple languages (including English and Swedish)
- 🚀 High-performance faster-whisper backend
- 🐳 Docker support for easy deployment
- 🔧 AMD GPU acceleration with CPU fallback
- 📝 RESTful API with FastAPI

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone or create the project:**
   ```bash
   git clone <your-repo> whisper-transcribe-api
   # OR create the directory and copy files
   mkdir whisper-transcribe-api && cd whisper-transcribe-api
   ```

2. **Build and run with Docker:**
   ```bash
   docker build -t whisper-transcribe-api .
   docker run -p 8000:8000 whisper-transcribe-api
   ```

3. **Or use docker-compose:**
   ```bash
   docker-compose up --build
   ```

### Option 2: Local Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python main.py
   # OR
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Usage

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /transcribe` - Transcribe audio file

### Sample Requests

1. **Basic transcription (auto-detect language):**
   ```bash
   curl -X POST "http://localhost:8000/transcribe" \
        -F "file=@your_audio.wav"
   ```

2. **Swedish audio transcription:**
   ```bash
   curl -X POST "http://localhost:8000/transcribe" \
        -F "file=@swedish_audio.wav" \
        -F "language=sv"
   ```

3. **Translate to English:**
   ```bash
   curl -X POST "http://localhost:8000/transcribe" \
        -F "file=@audio.wav" \
        -F "task=translate"
   ```

### Supported Audio Formats

- WAV, MP3, M4A, FLAC, OGG
- MP4, MOV, AVI (video files with audio)

### Example Response

```json
{
  "text": "Hello, this is a test transcription.",
  "language": "en",
  "language_probability": 0.99,
  "duration": 3.5,
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Hello, this is a test transcription.",
      "confidence": -0.2
    }
  ],
  "task": "transcribe"
}
```

## Configuration

### Environment Variables

- `WHISPER_MODEL_SIZE`: Model size (`tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`). Default: `base`
- `WHISPER_CACHE_DIR`: Directory to cache model files

### Model Sizes

| Model  | Parameters | English-only | Multilingual | Required VRAM | Relative Speed |
|--------|------------|--------------|--------------|---------------|----------------|
| tiny   | 39 M       | ✓            | ✓            | ~1 GB         | ~32x           |
| base   | 74 M       | ✓            | ✓            | ~1 GB         | ~16x           |
| small  | 244 M      | ✓            | ✓            | ~2 GB         | ~6x            |
| medium | 769 M      | ✓            | ✓            | ~5 GB         | ~2x            |
| large  | 1550 M     | ✗            | ✓            | ~10 GB        | 1x             |

### GPU Configuration

The service automatically detects and uses:
- **AMD GPU**: If available with ROCm/PyTorch
- **NVIDIA GPU**: If CUDA is available
- **CPU fallback**: Always available with optimized int8 quantization

For AMD GPU support on Arch Linux:
```bash
# Install ROCm (if not already installed)
sudo pacman -S rocm-opencl-runtime rocm-clang-ocl

# For PyTorch with ROCm support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
```

## Testing from Phone

You can easily test from your phone using apps like:
- **Termux** (Android): Use curl commands directly
- **Shortcuts** (iOS): Create a shortcut to record and upload audio
- **HTTP client apps**: Any app that can send POST requests with file uploads

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
# Build
docker build -t whisper-transcribe-api .

# Run with volume mount for development
docker run -p 8000:8000 -v $(pwd):/app whisper-transcribe-api

# View logs
docker logs <container_id>
```

## Troubleshooting

### Common Issues

1. **Model download fails**: Check internet connection, the model will be downloaded on first use
2. **GPU not detected**: Install proper GPU drivers (ROCm for AMD, CUDA for NVIDIA)
3. **Out of memory**: Use a smaller model size or switch to CPU-only mode
4. **Audio format not supported**: Convert to WAV/MP3 using ffmpeg

### Performance Tips

- Use `base` model for good balance of speed/accuracy
- Enable GPU acceleration for faster processing
- Use `tiny` model for real-time applications
- Consider `large-v3` for highest accuracy (requires more VRAM)

## License

This project uses OpenAI's Whisper model. Please check the original license terms.
