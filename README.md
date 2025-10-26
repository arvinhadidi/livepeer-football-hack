# 🎭 TintedGlasses AI

**Real-time AI video transformation powered by your emotions**

Transform live sports broadcasts into dynamic visual experiences that respond to your reactions in real-time. Built for the Encode Club x Livepeer Hackathon.

## 🎯 What It Does

TintedGlasses AI listens to your live commentary while watching sports and automatically transforms the video stream based on your emotional reactions:

- 😄 **Excited** → Explosive neon colors, dynamic motion blur, vibrant energy
- 😢 **Sad** → Melancholic blue tones, rain-soaked atmosphere, dramatic shadows  
- 😴 **Boring** → Vintage grayscale, film grain, minimalist aesthetic
- 😱 **Terrible** → Dramatic filters emphasizing the pain
- 😐 **Neutral** → Clean professional broadcast style

The system also plays mood-appropriate background music and displays visual overlays showing the current emotional state.

## 🎥 Demo

(https://youtu.be/MVe20EmvMn0?si=V26aAl01Ld29dGdo)

## ✨ Features

- **Voice-Reactive Visuals**: Real-time speech-to-text transcription detects emotional keywords
- **AI Video Transformation**: Livepeer Daydream API applies generative visual effects
- **Dynamic Mood Matching**: 5 distinct visual styles triggered by your reactions
- **Mood-Based Music**: Automatic background music selection that loops per mood
- **Live Overlays**: Text and image overlays showing current emotional state
- **Low Latency**: Updates visual style within 5-10 seconds of detection

## 🛠️ Tech Stack

- **Livepeer Daydream API** - Real-time AI video transformation
- **Livepeer Studio** - Video streaming infrastructure  
- **Faster-Whisper** - Real-time speech transcription
- **Python** - Backend processing
- **OBS Studio** - Video streaming and overlay management
- **Pygame** - Audio playback
- **SoundDevice** - Microphone capture

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- OBS Studio
- FFmpeg
- Daydream API key (get from [daydream.live](https://daydream.live))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/arvinhadidi/tintedglasses-ai.git
cd tintedglasses-ai
```

2. Create virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install faster-whisper sounddevice numpy pygame requests
```

3. Set up your Daydream API key:
```bash
export DAYDREAM_API_KEY="your_api_key_here"
```

4. Create folder structure for mood assets:
```
incredibles_audio/
├── excited/
│   └── song.mp3
├── sad/
│   └── song.mp3
├── boring/
│   └── song.mp3
├── neutral/
│   └── song.mp3
└── terrible/
    └── song.mp3

mood_images/
├── excited.png
├── sad.png
├── boring.png
├── neutral.png
└── terrible.png
```

### Running the Project

1. Start the script:
```bash
python daydream_mood_transform.py
```

2. Configure OBS when prompted:
   - Set WHIP streaming with provided URL
   - Add your video source
   - Add text overlay reading from `current_mood.txt` (white, bottom right)
   - Add image overlay from `current_mood.png` (bottom right)
   - Start streaming

3. Open the playback URL in your browser

4. Start watching and reacting! Say things like:
   - "Yes! Amazing goal!" → Excited mode
   - "Oh no, terrible miss!" → Terrible mode  
   - "This is so boring..." → Boring mode

## 🎨 How It Works

1. **Audio Capture**: Microphone continuously records your commentary
2. **Transcription**: Faster-Whisper transcribes speech in 5-second chunks
3. **Mood Detection**: Keyword matching identifies emotional state
4. **Visual Update**: Daydream API applies corresponding visual style via PATCH request
5. **Music & Overlays**: Background music switches and OBS overlays update
6. **Stream Output**: Transformed video plays on Livepeer network

## 🏗️ Architecture

```
Microphone Input → Faster-Whisper → Mood Detection
                                          ↓
OBS Video Source → Livepeer WHIP → Daydream API → Transformed Stream
                                          ↓
                              Music Player + Overlays
```

## 📁 Project Structure

```
tintedglasses-ai/
├── daydream_mood_transform.py    # Main application
├── incredibles_audio/             # Mood music files
├── mood_images/                   # Mood overlay images
├── current_mood.txt              # Auto-generated for OBS
├── current_mood.png              # Auto-generated for OBS
└── README.md
```

## 🎯 Use Cases

- **Live Sports Commentary**: Add emotional depth to your viewing experience
- **Streaming Content**: Create unique viewer experiences for Twitch/YouTube
- **Gaming**: React to gameplay with dynamic visual effects
- **Creative Performances**: Real-time visual art responding to voice/music

## 🔮 Future Enhancements

- Multi-language support
- Custom mood configurations
- Facial expression detection via webcam
- Social sharing of transformed clips
- Community mood presets

## 🏆 Built For

Encode Club x Livepeer Hackathon - Real-Time AI Video Track

## 📝 License

MIT

## 🙏 Acknowledgments

- Livepeer team for the amazing Daydream API
- Encode Club for hosting the hackathon
- OpenAI Whisper team for speech recognition technology

---

**Made with ❤️ for sports fans who feel deeply**