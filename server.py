from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
from datetime import datetime
import io

app = FastAPI()

# Store active WebSocket connections
active_connections: list[WebSocket] = []

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming audio"""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"Client connected. Total connections: {len(active_connections)}")
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()
            print(f"Received {len(data)} bytes at {datetime.now()}")
            
            # Process or save audio data here
            # For example, save to file:
            # with open(f"audio_{datetime.now().timestamp()}.raw", "ab") as f:
            #     f.write(data)
            
            # Echo back confirmation (optional)
            await websocket.send_json({
                "status": "received",
                "bytes": len(data),
                "timestamp": str(datetime.now())
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(active_connections)}")

@app.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """HTTP POST endpoint for uploading audio files"""
    contents = await file.read()
    
    # Save the audio file
    filename = f"audio_{datetime.now().timestamp()}_{file.filename}"
    with open(filename, "wb") as f:
        f.write(contents)
    
    return {
        "filename": filename,
        "size": len(contents),
        "content_type": file.content_type
    }

@app.post("/stream/audio")
async def stream_audio_post(file: UploadFile = File(...)):
    """HTTP POST endpoint for streaming audio in chunks"""
    chunk_size = 1024 * 64  # 64KB chunks
    
    async def audio_stream():
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    return StreamingResponse(
        audio_stream(),
        media_type=file.content_type or "audio/wav"
    )

@app.get("/")
async def root():
    return {
        "message": "FastAPI Audio Streaming Server",
        "endpoints": {
            "websocket": "/ws/audio",
            "upload": "/upload/audio",
            "stream": "/stream/audio"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
