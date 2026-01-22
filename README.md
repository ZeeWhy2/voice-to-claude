# Voice-to-Claude (VTC)

A lightweight system tray application that captures your voice, transcribes it using Whisper, and types the result directly into any active window.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Global Hotkey Recording** — Press a hotkey anywhere to start/stop recording
- **Whisper Transcription** — Use OpenAI's API or run Whisper locally
- **Auto-Type Output** — Transcribed text is typed directly into the focused window
- **Copy Last Transcription** — Quickly copy your last transcription to clipboard
- **Floating Status Overlay** — See when you're recording or processing
- **System Tray App** — Runs quietly in the background with easy access to settings

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/vtc.git
cd vtc

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Requirements

- Python 3.10 or higher
- Windows (macOS/Linux support may vary)
- A microphone

## Quick Start

1. **Run the app** — `python main.py`
2. **Configure on first launch** — Set your hotkeys and choose your transcription mode
3. **Press your record hotkey** — A floating overlay shows "Recording..."
4. **Speak**, then press the hotkey again to stop
5. **Watch your words appear** — Text is typed into whatever window is focused

## Configuration

On first run, the settings window opens automatically. You can also access it anytime by right-clicking the system tray icon.

| Setting | Description |
|---------|-------------|
| **Record Toggle** | Hotkey to start/stop recording (e.g., `ctrl+shift+r`) |
| **Copy Last** | Hotkey to copy last transcription to clipboard |
| **Input Device** | Select your microphone or use system default |
| **Whisper Mode** | `OpenAI API` (cloud) or `Local` (on-device) |
| **OpenAI API Key** | Required if using OpenAI mode |
| **Local Model** | Model size for local mode: `tiny`, `base`, `small`, `medium`, `large` |
| **Language** | Hint for transcription language (e.g., `en`, `es`, `fr`) |

### OpenAI vs Local Mode

| | OpenAI API | Local |
|---|---|---|
| **Speed** | Fast (depends on internet) | Depends on hardware |
| **Privacy** | Audio sent to OpenAI | Everything stays on device |
| **Cost** | ~$0.006/minute | Free |
| **Setup** | Just need API key | Downloads model on first use |

## Usage Tips

- **Dictate into any app** — Text editors, chat apps, browser fields, anywhere you can type
- **Quick corrections** — Use the copy hotkey to grab your last transcription and paste it elsewhere
- **Switch modes anytime** — Change between OpenAI and local in settings without restarting

## Project Structure

```
vtc/
├── main.py           # Application entry point
├── config.py         # Configuration management
├── recorder.py       # Audio recording
├── transcriber.py    # Whisper transcription (API + local)
├── hotkeys.py        # Global hotkey handling
├── typer.py          # Simulated typing output
├── overlay.py        # Status overlay window
├── tray.py           # System tray icon
├── settings_gui.py   # Settings dialog
└── requirements.txt  # Dependencies
```

## Troubleshooting

**No audio being recorded**
- Check that the correct input device is selected in settings
- Ensure your microphone permissions are enabled

**Transcription is slow**
- If using local mode, try a smaller model (`tiny` or `base`)
- If using OpenAI, check your internet connection

**Hotkeys not working**
- Some key combinations may be reserved by other apps
- Try a different combination in settings

**Text not typing**
- Ensure the target window is focused before recording stops
- Some applications may block simulated input

## License

MIT License — feel free to use, modify, and distribute.

---

Made for fast voice input without leaving your keyboard workflow.
