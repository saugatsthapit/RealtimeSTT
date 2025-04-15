# stt_websocket_server.py

from RealtimeSTT import AudioToTextRecorder
import websockets
import asyncio
import json
import queue
import threading
import sys
import os

# Set up the message queue and clients list
message_queue = queue.Queue()
connected_clients = set()
port = 5025  # You can change this port as needed

# Create an event to stop the server gracefully
stop_event = threading.Event()

# Callback function for real-time transcription updates
def on_transcription_update(text):
    # Send the real-time transcription to connected clients
    message = {
        "type": "realtime",
        "text": text
    }
    message_queue.put(message)
    print(f"Transcription update: {text}")

# Callback for when a full sentence is transcribed
def on_transcription_complete(text):
    # Send the full transcription to connected clients
    message = {
        "type": "full",
        "text": text
    }
    message_queue.put(message)
    print(f"Full transcription: {text}")

# Callback for recording events
def on_recording_start():
    message_queue.put({"type": "status", "status": "recording_started"})
    print("Recording started")

def on_recording_stop():
    message_queue.put({"type": "status", "status": "recording_stopped"})
    print("Recording stopped")

# WebSocket handler for client connections
async def client_handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    try:
        # Keep the connection open
        while not stop_event.is_set():
            # You can add message handling here if needed
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                # Process messages from clients if needed
                print(f"Received message from client: {len(message)} bytes")
                # If it's binary data (audio), print the first few bytes as hex
                if isinstance(message, bytes):
                    print(f"Audio data received: first 10 bytes: {message[:10].hex()}")
                    # We need to process the audio data here and pass it to the recorder
                    # For now, we'll just acknowledge receipt
                    ack_message = {"type": "status", "status": "audio_received", "size": len(message)}
                    await websocket.send(json.dumps(ack_message))
                else:
                    print(f"Text message: {message}")
            except asyncio.TimeoutError:
                # This is just a timeout for the recv, not an error
                pass
            except websockets.exceptions.ConnectionClosed:
                break
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

# Message sender task
async def message_sender():
    while not stop_event.is_set():
        # Send any messages in the queue to all clients
        while not message_queue.empty():
            message = message_queue.get()
            if connected_clients:
                print(f"Sending message to {len(connected_clients)} clients: {message}")
                for client in connected_clients.copy():
                    try:
                        await client.send(json.dumps(message))
                    except websockets.exceptions.ConnectionClosed:
                        # Client disconnected
                        try:
                            connected_clients.remove(client)
                        except KeyError:
                            pass  # Already removed
                    except Exception as e:
                        print(f"Error sending to client: {e}")
        # Small delay to prevent CPU hogging
        await asyncio.sleep(0.02)

# Initialize the audio recorder
def initialize_recorder(input_device_index=None):
    print("Initializing audio recorder...")
    
    recorder_config = {
        'spinner': False,
        'model': 'small.en',
        'language': 'en',
        'silero_sensitivity': 0.2,  # Increased for better voice pickup
        'post_speech_silence_duration': 1.0,
        'min_length_of_recording': 0.5,
        'enable_realtime_transcription': True,
        'realtime_processing_pause': 0.02,
        'realtime_model_type': 'tiny.en',
        'on_realtime_transcription_update': on_transcription_update,
    }
    
    # Add input device index if specified
    if input_device_index is not None:
        recorder_config['input_device_index'] = input_device_index
    
    # Create the recorder
    recorder = AudioToTextRecorder(**recorder_config)
    
    # Manually set up event callbacks if the API supports it
    try:
        # Try setting callbacks using class attributes or methods
        recorder.on_transcription_complete = on_transcription_complete
        recorder.on_recording_start = on_recording_start
        recorder.on_recording_stop = on_recording_stop
    except Exception as e:
        print(f"Warning: Could not set all callbacks: {e}")
    
    return recorder

# Recorder thread function
def recorder_thread(recorder):
    import time  # Import time module here
    print("Starting recorder thread...")
    while not stop_event.is_set():
        try:
            print("Waiting for audio...")
            text = recorder.text()
            on_transcription_complete(text)
        except Exception as e:
            print(f"Error in recorder thread: {e}")
            if stop_event.is_set():
                break
            # Small delay before retrying
            time.sleep(1)

async def main():
    # Parse command line arguments
    input_device = None
    if len(sys.argv) > 1:
        try:
            input_device = int(sys.argv[1])
            print(f"Using input device index: {input_device}")
        except ValueError:
            print(f"Invalid input device index: {sys.argv[1]}")
    
    # Initialize the recorder
    recorder = initialize_recorder(input_device)
    
    # Start the recorder thread
    rec_thread = threading.Thread(target=recorder_thread, args=(recorder,))
    rec_thread.daemon = True
    rec_thread.start()
    
    # Start the WebSocket server
    async with websockets.serve(client_handler, "127.0.0.1", port) as server:
        print(f"WebSocket server started at ws://127.0.0.1:{port}")
        print("Waiting for client connections...")
        
        # Start the message sender task
        sender_task = asyncio.create_task(message_sender())
        
        try:
            # Keep the server running until interrupted
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            # Clean up
            stop_event.set()
            sender_task.cancel()
            try:
                await sender_task
            except asyncio.CancelledError:
                pass
            print("Server shut down")

if __name__ == "__main__":
    import time
    
    print("Starting STT WebSocket Server")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
        stop_event.set()