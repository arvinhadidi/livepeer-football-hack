import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import cv2
from faster_whisper import WhisperModel
import subprocess

# Configuration
VIDEO_PATH = "input_vids/122_starting.mp4"  # Change this to your video path
OUTPUT_PATH = "output_vids/122_starting_transcribed.mp4"
WHISPER_MODEL = "tiny"  # Options: tiny, base, small, medium, large-v3

def extract_audio(video_path):
    """Extract audio from video to temp file"""
    audio_path = "temp_audio.wav"
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1',
        audio_path, '-y'
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def transcribe_audio(audio_path):
    """Transcribe audio using faster-whisper"""
    print("Loading Whisper model...")
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    
    print("Transcribing audio...")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    transcriptions = []
    for segment in segments:
        transcriptions.append({
            'start': segment.start,
            'end': segment.end,
            'text': segment.text
        })
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
    
    return transcriptions

def overlay_text_on_video(video_path, transcriptions, output_path):
    """Add transcription overlay to video"""
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    print("Processing video frames...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        current_time = frame_count / fps
        
        # Find active transcription for current time
        current_text = ""
        for trans in transcriptions:
            if trans['start'] <= current_time <= trans['end']:
                current_text = trans['text']
                break
        
        # Draw text overlay
        if current_text:
            # Black background box for text
            text_size = cv2.getTextSize(current_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            box_coords = ((10, height - 60), (text_size[0] + 20, height - 10))
            cv2.rectangle(frame, box_coords[0], box_coords[1], (0, 0, 0), -1)
            
            # White text
            cv2.putText(frame, current_text, (15, height - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        out.write(frame)
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")
    
    cap.release()
    out.release()
    print(f"Output saved to {output_path}")

def main():
    # Extract audio
    audio_path = extract_audio(VIDEO_PATH)
    
    # Transcribe
    transcriptions = transcribe_audio(audio_path)
    
    # Overlay on video
    overlay_text_on_video(VIDEO_PATH, transcriptions, OUTPUT_PATH)
    
    # Cleanup
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    print("Done!")

if __name__ == "__main__":
    main()