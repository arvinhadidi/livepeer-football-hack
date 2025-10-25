import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import requests
import json
import time
from faster_whisper import WhisperModel
import subprocess

# Configuration
DAYDREAM_API_KEY = os.getenv("DAYDREAM_API_KEY")  # Get from daydream.live
VIDEO_PATH = "input_vids/113.mp4"
if not os.path.exists(VIDEO_PATH):
    print(f"File not found: {VIDEO_PATH}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in input_vids: {os.listdir('input_vids')}")
WHISPER_MODEL = "base"

# Mood-based visual styles
MOOD_STYLES = {
    "excited": {
        "prompt": "explosive energy, vibrant neon colors, dynamic motion blur, electrifying atmosphere, intense action",
        "negative_prompt": "calm, muted, static, boring",
        "num_inference_steps": 40,
        "seed": 42
    },
    "sad": {
        "prompt": "melancholic blue tones, rain-soaked atmosphere, somber mood, dramatic shadows, emotional depth",
        "negative_prompt": "bright, cheerful, colorful, happy",
        "num_inference_steps": 45,
        "seed": 123
    },
    "boring": {
        "prompt": "muted grayscale, vintage film grain, slow motion aesthetic, minimalist composition, subdued atmosphere",
        "negative_prompt": "vibrant, exciting, dynamic, colorful",
        "num_inference_steps": 35,
        "seed": 999
    }
}

# Keywords to detect mood
MOOD_KEYWORDS = {
    "excited": ["goal", "score", "amazing", "incredible", "wow", "brilliant", "fantastic"],
    "sad": ["miss", "lost", "defeat", "disappointed", "unfortunate", "poor"],
    "boring": ["slow", "uneventful", "nothing", "quiet", "waiting", "stalled"]
}

def transcribe_audio(video_path):  # Change parameter name
    """Transcribe audio using faster-whisper"""
    print("Loading Whisper model...")
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    
    print("Transcribing audio...")
    segments, info = model.transcribe(video_path, beam_size=5)  # Pass video directly
    
    transcriptions = []
    for segment in segments:
        transcriptions.append({
            'start': segment.start,
            'end': segment.end,
            'text': segment.text.lower()
        })
    
    return transcriptions

# In main(), remove the extract_audio line:
def main():
    # transcriptions = transcribe_audio(audio_path)  # OLD
    transcriptions = transcribe_audio(VIDEO_PATH)  # NEW - pass video directly

def detect_mood(transcriptions):
    """Detect mood changes throughout video based on transcription"""
    mood_timeline = []
    
    for trans in transcriptions:
        text = trans['text']
        detected_mood = "boring"  # default
        
        # Check for mood keywords
        for mood, keywords in MOOD_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                detected_mood = mood
                break
        
        mood_timeline.append({
            'start': trans['start'],
            'end': trans['end'],
            'mood': detected_mood,
            'text': trans['text']
        })
        
        print(f"[{trans['start']:.1f}s] Mood: {detected_mood} - '{trans['text']}'")
    
    return mood_timeline

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
    
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print(f"Stream created: {result['id']}")
        print(f"WHIP URL: {result['whip_url']}")
        print(f"Playback ID: {result['output_playback_id']}")
        print(f"Watch at: https://lvpr.tv/?v={result['output_playback_id']}")
        return result
    else:
        print(f"Error creating stream: {response.status_code}")
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
    
    print(f"\nUpdating to {mood.upper()} mood...")
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✓ Stream updated to {mood} style")
        return True
    else:
        print(f"Error updating stream: {response.status_code}")
        print(response.text)
        return False

def generate_mood_change_script(mood_timeline, output_file="mood_changes.txt"):
    """Generate a script showing when to change moods"""
    with open(output_file, 'w') as f:
        f.write("MOOD CHANGE TIMELINE\n")
        f.write("=" * 50 + "\n\n")
        
        current_mood = None
        for entry in mood_timeline:
            if entry['mood'] != current_mood:
                f.write(f"[{entry['start']:.1f}s] Switch to: {entry['mood'].upper()}\n")
                f.write(f"  Trigger: '{entry['text']}'\n\n")
                current_mood = entry['mood']
    
    print(f"\nMood change script saved to {output_file}")

def main():
    print("=== Daydream Mood-Based Video Transform ===\n")
    
    # Step 1: Transcribe video
    transcriptions = transcribe_audio(VIDEO_PATH)
    
    # Step 2: Detect moods
    mood_timeline = detect_mood(transcriptions)
    generate_mood_change_script(mood_timeline)
    
    # Step 3: Create Daydream stream
    stream = create_daydream_stream()
    if not stream:
        return
    
    stream_id = stream['id']
    
    print("\n" + "=" * 50)
    print("SETUP INSTRUCTIONS:")
    print("=" * 50)
    print("1. Open OBS and configure WHIP streaming:")
    print(f"   - Service: WHIP")
    print(f"   - Server: {stream['whip_url']}")
    print(f"   - Leave Bearer Token blank")
    print("2. Add your video as a Media Source in OBS")
    print("3. Start streaming in OBS")
    print(f"4. Watch output at: https://lvpr.tv/?v={stream['output_playback_id']}")
    print("\nPress Enter when stream is running...")
    input()
    
    # Step 4: Apply mood changes in real-time
    print("\n=== Starting Mood-Based Transformation ===\n")
    print("Waiting 5 seconds for stream to stabilize...")
    time.sleep(5)
    
    current_mood = None
    for entry in mood_timeline:
        if entry['mood'] != current_mood:
            update_stream_mood(stream_id, entry['mood'])
            current_mood = entry['mood']
            
            # Wait until next mood change
            if mood_timeline.index(entry) < len(mood_timeline) - 1:
                next_entry = mood_timeline[mood_timeline.index(entry) + 1]
                wait_time = next_entry['start'] - entry['start']
                print(f"Waiting {wait_time:.1f}s until next mood change...")
                time.sleep(wait_time)
    
    print("\n✓ All mood changes applied!")
    print(f"Stream ID: {stream_id}")
    print("Keep OBS running to continue viewing the output")
    
    # # Cleanup
    # if os.path.exists(audio_path):
    #     os.remove(audio_path)

if __name__ == "__main__":
    main()