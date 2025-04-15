#!/usr/bin/env python3
# test_websocket.py - A simple test script for the WebSocket server

import asyncio
import websockets
import json
import sys
import time
import random
import os
import signal

# Generate some random audio-like data for testing
def generate_fake_audio(size=1600):
    return bytes([random.randint(0, 255) for _ in range(size)])

async def test_connection():
    uri = "ws://127.0.0.1:5025"
    print(f"Attempting to connect to {uri}...")
    print("Opening WebSocket connection...")
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("Connected to WebSocket server!")
            
            # Send a test message
            print("Sending a test message...")
            await websocket.send(json.dumps({"type": "test", "message": "Hello from test client"}))
            
            # Send some fake audio data
            for i in range(5):
                audio_data = generate_fake_audio()
                print(f"Sending {len(audio_data)} bytes of fake audio data (chunk {i+1}/5)...")
                await websocket.send(audio_data)
                
                # Wait for a response
                print("Waiting for server response...")
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"Received response: {response}")
                except asyncio.TimeoutError:
                    print("Warning: Timeout waiting for response, but continuing...")
                
                # Wait briefly between sends
                await asyncio.sleep(0.5)
            
            print("Test complete")
            
    except websockets.exceptions.ConnectionRefusedError:
        print("Error: Connection refused. Is the WebSocket server running?")
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Make sure the server is running: python stt_websocket_server.py")
        print("2. Check if port 5025 is blocked by firewall")
        print("3. Try running both client and server as administrator")
        return False
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Error: {e}")
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Make sure the server is running: python stt_websocket_server.py")
        print("2. Check if port 5025 is blocked by firewall")
        print("3. Try running both client and server as administrator")
        print("4. Ensure no other application is using port 5025")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

def signal_handler(sig, frame):
    print("\nTest interrupted by user. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handling for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting WebSocket client test...")
    result = asyncio.run(test_connection())
    
    if result:
        print("Test completed successfully!")
    else:
        print("Test failed!")
        sys.exit(1) 