import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import requests
import time
import queue
import threading
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import wave
import pygame
import random

# Configuration
DAYDREAM_API_KEY = os.getenv("DAYDREAM_API_KEY")
WHISPER_MODEL = "base"
SAMPLE_RATE = 16000
CHUNK_DURATION = 5  # Process audio every 5 seconds
AUDIO_FOLDER = "incredibles_audio"  # Folder with mood music files

# Mood-based visual styles
MOOD_STYLES = {
    "excited": {
        "prompt": "explosive energy, vibrant neon colors, high quality, electrifying atmosphere, intense action, yellow bright sunshine colours, bright",
        "negative_prompt": "calm, muted, static, boring, dull, dark",
        "num_inference_steps": 45,
    },
    "sad": {
        "prompt": "muted grayscale, melancholic dark grey tones, rain-soaked atmosphere, somber mood, dramatic shadows, emotional depth, dark, grey",
        "negative_prompt": "bright, cheerful, colorful, happy",
        "num_inference_steps": 45,
    },
    "boring": {
        "prompt": "light brown, vintage film grain, slow motion aesthetic, minimalist composition, subdued atmosphere",
        "negative_prompt": "vibrant, exciting, dynamic, colorful",
        "num_inference_steps": 35,
    },
    "neutral": {
        "prompt": "clean broadcast style, professional sports coverage, balanced colors",
        "negative_prompt": "distorted, ugly, low quality",
        "num_inference_steps": 40,
    }, 
    "terrible": { 
        "prompt": "dark, dreary, doom, depression",
        "negative_prompt": "bright, cheerful, colorful, happy, amazing",
        "num_inference_steps": 30, 
    }
}

# Keywords to detect mood from your reactions
MOOD_KEYWORDS = {
    "excited": ["yes", "wow", "amazing", "incredible", "goal", "score", "oh my god", "lets go", "come on"],
    "sad": ["no", "oh no", "damn", "miss"],
    "boring": ["slow", "nothing", "boring", "meh", "whatever", "waiting"],
    "terrible": ["unfortunate", "terrible", "awful"]
}

class AudioRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
    def callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())
    
    def start_recording(self):
        """Start recording from microphone"""
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.callback,
            blocksize=int(SAMPLE_RATE * 0.5)  # 0.5 second blocks
        )
        self.stream.start()
        print("🎤 Microphone recording started")
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        print("🎤 Microphone recording stopped")
    
    def get_audio_chunk(self, duration):
        """Get audio data for specified duration"""
        frames = []
        num_frames = int(SAMPLE_RATE * duration / (SAMPLE_RATE * 0.5))
        
        for _ in range(num_frames):
            try:
                data = self.audio_queue.get(timeout=1)
                frames.append(data)
            except queue.Empty:
                break
        
        if frames:
            return np.concatenate(frames)
        return None

class MoodMusicPlayer:
    def __init__(self, audio_folder):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.music.set_volume(0.5)  # 50% volume
        self.audio_folder = audio_folder
        self.current_mood = None
        self.mood_files = self._load_mood_files()
        
    def _load_mood_files(self):
        """Load audio files for each mood"""
        mood_files = {}
        
        if not os.path.exists(self.audio_folder):
            print(f"⚠️  Audio folder '{self.audio_folder}' not found. Music disabled.")
            return mood_files
        
        for mood in MOOD_STYLES.keys():
            mood_dir = os.path.join(self.audio_folder, mood)
            if os.path.exists(mood_dir):
                files = [f for f in os.listdir(mood_dir) 
                        if f.endswith(('.mp3', '.wav', '.ogg'))]
                if files:
                    mood_files[mood] = [os.path.join(mood_dir, f) for f in files]
                    print(f"🎵 Loaded {len(files)} audio files for '{mood}' mood")
        
        return mood_files
    
    def play_mood(self, mood):
        """Play music for specified mood (loops until changed)"""
        if mood == self.current_mood:
            return  # Already playing this mood
        
        self.current_mood = mood
        
        if mood not in self.mood_files or not self.mood_files[mood]:
            print(f"⚠️  No audio files found for '{mood}' mood")
            pygame.mixer.music.stop()
            return
        
        # Pick random song from mood folder
        song = random.choice(self.mood_files[mood])
        print(f"🎵 Playing: {os.path.basename(song)}")
        
        try:
            pygame.mixer.music.load(song)
            pygame.mixer.music.play(-1)  # -1 = loop forever
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
    
    def stop(self):
        """Stop music playback"""
        pygame.mixer.music.stop()
        self.current_mood = None

def save_audio_chunk(audio_data, filename="temp_chunk.wav"):
    """Save audio data to WAV file for Whisper"""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
    return filename

def transcribe_chunk(audio_file, model):
    """Transcribe audio chunk"""
    segments, info = model.transcribe(audio_file, beam_size=5)
    
    text = ""
    for segment in segments:
        text += segment.text.lower() + " "
    
    return text.strip()

def detect_mood_from_text(text):
    """Detect mood from transcribed text"""
    if not text:
        return "neutral"
    
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            print(f"🎯 Detected '{mood}' from: '{text}'")
            return mood
    
    return "neutral"

def create_daydream_stream(pipeline_id="pip_SD-turbo"):
    """Create a Daydream stream"""
    url = "https://api.daydream.live/v1/streams"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DAYDREAM_API_KEY}"
    }
    data = {"pipeline_id": pipeline_id}
    
    print("Creating Daydream stream...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ Stream created: {result['id']}")
        print(f"\n📺 WHIP URL: {result['whip_url']}")
        print(f"👀 Watch at: https://lvpr.tv/?v={result['output_playback_id']}\n")
        return result
    else:
        print(f"❌ Error creating stream: {response.status_code}")
        print(response.text)
        return None

def update_stream_mood(stream_id, mood):
    """Update Daydream stream with mood-based parameters"""
    url = f"https://api.daydream.live/v1/streams/{stream_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DAYDREAM_API_KEY}"
    }
    
    style = MOOD_STYLES[mood]
    data = {"params": style}
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ Stream updated to {mood.upper()} mood")
        return True
    else:
        print(f"❌ Error updating stream: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("🎮 DAYDREAM LIVE REACTION-BASED VIDEO TRANSFORM")
    print("=" * 60)
    
    # Create Daydream stream
    stream = create_daydream_stream()
    if not stream:
        return
    
    stream_id = stream['id']
    
    print("SETUP INSTRUCTIONS:")
    print("-" * 60)
    print("1. Open OBS")
    print("2. Settings → Stream:")
    print(f"   - Service: WHIP")
    print(f"   - Server: {stream['whip_url']}")
    print(f"   - Bearer Token: (leave blank)")
    print("3. Add video source (your game footage)")
    print("4. Click 'Start Streaming'")
    print(f"5. Open in browser: https://lvpr.tv/?v={stream['output_playback_id']}")
    print("-" * 60)
    print("\nPress ENTER when OBS is streaming...")
    input()
    
    # Initialize
    print("\n🔄 Loading Whisper model...")
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    recorder = AudioRecorder()
    music_player = MoodMusicPlayer(AUDIO_FOLDER)
    
    print("✓ Ready to listen to your reactions!\n")
    print("=" * 60)
    print("CONTROLS:")
    print("- React naturally to the game (excited, sad, bored)")
    print("- Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Start recording
    recorder.start_recording()
    current_mood = "neutral"
    update_stream_mood(stream_id, current_mood)
    music_player.play_mood(current_mood)
    
    try:
        while True:
            # Get audio chunk
            print(f"🎧 Listening for {CHUNK_DURATION} seconds...")
            audio_chunk = recorder.get_audio_chunk(CHUNK_DURATION)
            
            if audio_chunk is not None and len(audio_chunk) > 0:
                # Save and transcribe
                audio_file = save_audio_chunk(audio_chunk)
                text = transcribe_chunk(audio_file, model)
                
                if text:
                    print(f"💬 You said: '{text}'")
                    
                    # Detect mood
                    new_mood = detect_mood_from_text(text)
                    
                    # Update if mood changed
                    if new_mood != current_mood:
                        print(f"\n🎨 Mood change: {current_mood} → {new_mood}")
                        update_stream_mood(stream_id, new_mood)
                        music_player.play_mood(new_mood)
                        current_mood = new_mood
                        print()
                else:
                    print("🔇 No speech detected")
                
                # Cleanup temp file
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        recorder.stop_recording()
        music_player.stop()
        print(f"\n✓ Stream ID: {stream_id}")
        print("Keep OBS running to continue viewing the output")

if __name__ == "__main__":
    main()