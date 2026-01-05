# Text-to-Speech (TTS) Features for Ocat

Ocat now includes built-in text-to-speech functionality using OpenAI's TTS API. This allows you to convert assistant responses to speech and play them directly through your terminal.

## Commands

### `/speak` (alias: `/s`)

Converts the last assistant response to speech using the default voice and model settings.

**Usage:**
```
/speak                    # Use default voice and model
/speak nova               # Use nova voice with default model  
/speak fable tts-1-hd     # Use fable voice with tts-1-hd model
```

### `/speaklike` (alias: `/sl`)

Converts the last assistant response to speech with custom instructions for how it should be spoken.

**Usage:**
```
/speaklike "speak slowly and clearly"
/speaklike "speak in an excited tone" nova
/speaklike "read this like a news anchor" fable tts-1-hd
```

## Configuration

Add TTS settings to your `ocat.yaml` configuration file:

```yaml
tts:
  enabled: true              # Enable/disable TTS functionality
  voice: "nova"              # Default voice (see available voices below)
  model: "tts-1"             # Default model (tts-1 or tts-1-hd)
  audio_dir: "/tmp"          # Directory to store MP3 files
```

### Available Voices

- `alloy` - Balanced and versatile
- `echo` - Clear and expressive
- `fable` - Warm and engaging
- `nova` - Friendly and conversational (default)
- `onyx` - Deep and authoritative
- `shimmer` - Bright and energetic

### Available Models

- `tts-1` - Standard quality, faster generation (default)
- `tts-1-hd` - Higher quality, slower generation

## Prerequisites

1. **OpenAI API Key**: Set the `OPENAI_API_KEY` environment variable
2. **Audio Player**: Install one of the following system audio players:
   - **Linux**: `mpg123`, `ffplay`, `aplay`, or `paplay`
   - **macOS**: `afplay` (built-in)
   - **Windows**: Uses built-in `start` command

## Audio Storage

- MP3 files are saved to the directory specified in `tts.audio_dir` (default: `/tmp`)
- Files are named with timestamps: `ocat_tts_<timestamp>.mp3`
- Files are played immediately and remain available for later playback

## Text Processing

The TTS system automatically cleans markdown formatting from responses:
- Removes code blocks (replaced with "[code block]")
- Strips markdown formatting (bold, italic, links, headers)
- Removes list markers
- Normalizes whitespace

## Examples

1. **Basic usage:**
   ```
   User: What is Python?
   Assistant: Python is a high-level programming language...
   User: /speak
   🔊 Generating speech using nova voice...
   🎵 Audio saved to: /tmp/ocat_tts_1234567890.mp3
   🎧 Playing audio...
   ✅ Audio playback completed
   ```

2. **Custom voice:**
   ```
   User: /speak fable
   🔊 Generating speech using fable voice...
   ```

3. **Custom instructions:**
   ```
   User: /speaklike "speak like a robot" onyx tts-1-hd
   🔊 Generating speech using onyx voice...
   ```

## Error Handling

The TTS commands will show helpful error messages for common issues:
- TTS disabled in configuration
- No assistant response found
- Invalid voice or model names
- Missing OpenAI API key
- Audio player not found
- Network or API errors

## Performance Notes

- `tts-1` model is faster but lower quality
- `tts-1-hd` model is slower but higher quality
- Large responses may take longer to generate
- Audio playback happens asynchronously

## Troubleshooting

**"No suitable audio player found"**
- Install an audio player: `sudo apt install mpg123` (Linux) or `brew install ffmpeg` (macOS)

**"OPENAI_API_KEY environment variable not set"**
- Set your API key: `export OPENAI_API_KEY="your-key-here"`

**"TTS is disabled in configuration"**
- Set `tts.enabled: true` in your `ocat.yaml` file

**Audio doesn't play**
- Check your system volume
- Verify the audio file was created in the specified directory
- Try playing the MP3 file manually to test your audio setup
