# save as test_audio.py
from RealtimeSTT import AudioToTextRecorder
import time

if __name__ == '__main__':
    print("Initializing recorder...")
    recorder = AudioToTextRecorder(
        spinner=True,
        language="en",
        model="base",  # Use a smaller model for faster loading
        debug_mode=True  # Enable debug output
    )
    
    print("Starting recording. Please speak...")
    recorder.start()
    
    # Record for 5 seconds
    time.sleep(5)
    
    print("Stopping recording and transcribing...")
    result = recorder.stop()
    
    print(f"Transcription: {result.text()}")
    
    # Clean up
    recorder.shutdown()