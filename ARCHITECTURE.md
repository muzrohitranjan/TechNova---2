# Real-Time Voice Recipe AI Architecture

## Pipeline Flow
```
Frontend Record → WebSocket audio blob (webm)
     ↓
Backend Whisper STT → text transcript
     ↓
GPT-4o-mini + JSON Schema → structured recipe
     ↓
gTTS → MP3 audio bytes
     ↓
WebSocket response → Frontend play + JSON UI
```

## Components
**Backend (`app/`)**:
- `voice_service.py`: ST
