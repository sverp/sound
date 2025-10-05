import asyncio
import websockets
import subprocess
import requests
import json

# Configuration
SERVER_URL = "192.168.0.108"  # Your laptop's IP address
SERVER_PORT = 8000
WS_URL = f"ws://{SERVER_URL}:{SERVER_PORT}/ws/audio"
HTTP_URL = f"http://{SERVER_URL}:{SERVER_PORT}/upload/audio"

# Audio recording settings
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK_SIZE = 4096

async def stream_audio_websocket():
    """Stream audio to server via WebSocket"""
    print(f"Connecting to WebSocket: {WS_URL}")
    
    # Start audio recording using termux-microphone-record
    # For continuous streaming, we'll use arecord or sox
    process = subprocess.Popen(
        ['termux-microphone-record', '-l', '0'],  # Unlimited recording
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("Connected! Streaming audio...")
            
            # Alternative: Use sox for more control
            # process = subprocess.Popen(
            #     ['sox', '-t', 'alsa', 'default', '-t', 'raw', '-'],
            #     stdout=subprocess.PIPE
            # )
            
            while True:
                # Read audio chunk
                audio_chunk = process.stdout.read(CHUNK_SIZE)
                
                if not audio_chunk:
                    break
                
                # Send to server
                await websocket.send(audio_chunk)
                
                # Receive confirmation (optional)
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=0.1
                    )
                    print(f"Server response: {response}")
                except asyncio.TimeoutError:
                    pass
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()

def record_and_upload():
    """Record audio file and upload via HTTP POST"""
    import tempfile
    import os
    
    print("Recording audio for 5 seconds...")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Record audio using termux-microphone-record
        subprocess.run([
            'termux-microphone-record',
            '-f', tmp_path,
            '-l', '5'  # Record for 5 seconds
        ], check=True)
        
        print(f"Recording saved to {tmp_path}")
        print(f"Uploading to {HTTP_URL}...")
        
        # Upload the file
        with open(tmp_path, 'rb') as f:
            files = {'file': ('audio.wav', f, 'audio/wav')}
            response = requests.post(HTTP_URL, files=files)
            
        print(f"Upload response: {response.json()}")
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def stream_with_ffmpeg():
    """Stream audio using ffmpeg (more reliable)"""
    import requests
    
    print("Starting audio stream with ffmpeg...")
    
    # Use ffmpeg to capture and stream
    cmd = [
        'ffmpeg',
        '-f', 'android_camera',
        '-i', '0:0',  # Audio input
        '-f', 'wav',
        '-'
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    
    try:
        # Stream chunks to server
        while True:
            chunk = process.stdout.read(CHUNK_SIZE)
            if not chunk:
                break
            
            # Send via HTTP POST
            response = requests.post(
                HTTP_URL,
                files={'file': ('stream.wav', chunk, 'audio/wav')}
            )
            print(f"Sent {len(chunk)} bytes")
            
    except KeyboardInterrupt:
        print("\nStopping stream...")
    finally:
        process.terminate()

if __name__ == "__main__":
    import sys
    
    print("Termux Audio Streaming Client")
    print("1. WebSocket streaming (continuous)")
    print("2. HTTP upload (record and send)")
    print("3. FFmpeg streaming")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(stream_audio_websocket())
    elif choice == "2":
        record_and_upload()
    elif choice == "3":
        stream_with_ffmpeg()
    else:
        print("Invalid choice")
