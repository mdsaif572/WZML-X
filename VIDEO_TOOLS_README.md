# 🎬 Video Tools Module for WZML-X Bot

A comprehensive video processing module that provides advanced video manipulation capabilities using FFmpeg integration.

## 📋 Features

### 🔍 Video Analysis
- **Video Information** - Get detailed metadata about video files
- **Format Detection** - Automatic format and codec identification
- **Stream Analysis** - Separate video and audio stream information

### 🎞️ Video Processing
- **Video Compression** - Multiple quality presets (low/medium/high/ultra)
- **Format Conversion** - Support for MP4, MKV, AVI, WebM, MOV
- **Video Trimming** - Cut videos by time range or duration
- **Resolution Changing** - Resize videos to different resolutions
- **Thumbnail Extraction** - Generate thumbnails at specific timestamps

### 🎵 Audio & Media Extraction
- **Audio Extraction** - Extract audio in MP3, AAC, FLAC, WAV formats
- **Subtitle Extraction** - Extract embedded subtitles
- **Watermark Addition** - Add image watermarks to videos
- **Video Merging** - Combine multiple videos into one

## 🚀 Available Commands

### Information Commands
| Command | Aliases | Description |
|---------|---------|-------------|
| `/vinfo` | `/vi` | Get detailed video information |
| `/vhelp` | `/vh` | Show video tools help |

### Processing Commands
| Command | Aliases | Description | Usage |
|---------|---------|-------------|-------|
| `/vcompress` | `/vc` | Compress video | `/vcompress <quality>` |
| `/vconvert` | `/vcv` | Convert video format | `/vconvert <format>` |
| `/vtrim` | `/vtr` | Trim video | `/vtrim <start> [duration]` |
| `/vresize` | `/vr` | Change resolution | `/vresize <resolution>` |

### Extraction Commands
| Command | Aliases | Description | Usage |
|---------|---------|-------------|-------|
| `/vaudio` | `/va` | Extract audio | `/vaudio [format]` |
| `/vthumb` | `/vt` | Extract thumbnail | `/vthumb [timestamp]` |

## 📖 Detailed Usage Guide

### 🔍 Video Information (`/vinfo`)
Get comprehensive information about any video file.

```
/vinfo (reply to video)
```

**Output includes:**
- File size and duration
- Video codec and resolution
- Frame rate and bitrate
- Audio codec and sample rate
- Channel information

### 🗜️ Video Compression (`/vcompress`)
Compress videos with different quality presets.

```
/vcompress <quality> (reply to video)
```

**Quality Options:**
- `low` - Fast compression, larger file size (CRF 28)
- `medium` - Balanced compression (CRF 23) [Default]
- `high` - Better quality, slower (CRF 18)
- `ultra` - Best quality, very slow (CRF 15)

**Examples:**
```
/vcompress medium
/vcompress high
```

### 🔄 Format Conversion (`/vconvert`)
Convert videos between different formats.

```
/vconvert <format> (reply to video)
```

**Supported Formats:**
- `mp4` - H.264/AAC (Most compatible)
- `mkv` - H.264/AAC (High quality container)
- `avi` - XviD/MP3 (Legacy format)
- `webm` - VP9/Opus (Web optimized)
- `mov` - H.264/AAC (Apple format)

**Examples:**
```
/vconvert mp4
/vconvert webm
```

### ✂️ Video Trimming (`/vtrim`)
Cut videos by specifying start time and duration/end time.

```
/vtrim <start_time> [duration_or_end_time] (reply to video)
```

**Time Formats:**
- `HH:MM:SS` (e.g., 00:01:30)
- `MM:SS` (e.g., 01:30)
- `seconds` (e.g., 90)

**Examples:**
```
/vtrim 00:00:30                    # From 30 seconds to end
/vtrim 00:00:30 00:01:00          # From 30s for 1 minute
/vtrim 30 60                      # From 30s for 60 seconds
/vtrim 00:01:00 00:02:30          # From 1:00 to 2:30
```

### 📐 Resolution Changing (`/vresize`)
Change video resolution while maintaining aspect ratio.

```
/vresize <resolution> (reply to video)
```

**Resolution Options:**
- `360p` or `640x360` - Low quality
- `480p` or `854x480` - SD quality
- `720p` or `1280x720` - HD quality
- `1080p` or `1920x1080` - Full HD
- `4k` or `3840x2160` - Ultra HD
- Custom: `WIDTHxHEIGHT` (e.g., 1600x900)

**Examples:**
```
/vresize 720p
/vresize 1280x720
/vresize 1080p
```

### 🎵 Audio Extraction (`/vaudio`)
Extract audio from videos in various formats.

```
/vaudio [format] (reply to video)
```

**Audio Formats:**
- `mp3` - MP3 format (192 kbps) [Default]
- `aac` - AAC format (128 kbps)
- `flac` - FLAC lossless format
- `wav` - WAV uncompressed format

**Examples:**
```
/vaudio mp3
/vaudio flac
```

### 🖼️ Thumbnail Extraction (`/vthumb`)
Extract thumbnail images from videos at specific timestamps.

```
/vthumb [timestamp] (reply to video)
```

**Examples:**
```
/vthumb                           # Extract at 5 seconds (default)
/vthumb 00:01:30                 # Extract at 1 minute 30 seconds
/vthumb 120                      # Extract at 120 seconds
```

## ⚙️ Requirements

### System Requirements
- **FFmpeg** - Must be installed and available in system PATH
- **Python 3.7+** - Required for async operations
- **Sufficient Storage** - For temporary file processing

### Python Dependencies
```
pyrogram
aiofiles
asyncio
```

## 🛠️ Installation & Setup

### 1. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to system PATH

**macOS:**
```bash
brew install ffmpeg
```

### 2. Verify Installation
```bash
ffmpeg -version
ffprobe -version
```

### 3. Bot Configuration
The video tools module is automatically loaded when the bot starts. No additional configuration is required.

## 🎯 Usage Tips

### Performance Optimization
- **File Size**: Larger videos take longer to process
- **Quality vs Speed**: Lower quality settings process faster
- **Format Choice**: MP4 is generally fastest for conversion
- **Resolution**: Downscaling is faster than upscaling

### Best Practices
- Use `medium` quality for balanced compression
- Convert to MP4 for maximum compatibility
- Extract thumbnails before heavy processing
- Trim videos before other operations to save time

### Troubleshooting
- **FFmpeg not found**: Ensure FFmpeg is installed and in PATH
- **Processing failed**: Check video file integrity
- **Large files**: Consider trimming or compressing first
- **Slow processing**: Use lower quality settings

## 📊 Quality Guidelines

| Quality | CRF | Speed | File Size | Use Case |
|---------|-----|-------|-----------|----------|
| Low | 28 | Fast | Large | Quick processing |
| Medium | 23 | Moderate | Balanced | General use |
| High | 18 | Slow | Small | Quality priority |
| Ultra | 15 | Very Slow | Smallest | Archive/storage |

## 🔧 Advanced Features

### Batch Processing
- Process multiple videos by using commands sequentially
- Each video is processed independently

### Format Compatibility
- Input: Most video formats supported by FFmpeg
- Output: Optimized for common formats (MP4, MKV, etc.)

### Error Handling
- Automatic cleanup of temporary files
- Detailed error messages for troubleshooting
- Graceful handling of interrupted operations

## 📝 Notes

- All processing is done server-side
- Temporary files are automatically cleaned up
- Processing time varies based on video size and complexity
- Commands require replying to a video message
- Authorization is required for all video tool commands

## 🆘 Support

For issues or feature requests related to video tools:
1. Check FFmpeg installation
2. Verify video file integrity
3. Review command syntax
4. Check bot logs for detailed error messages

---

**Video Tools Module** - Part of WZML-X Bot
*Powered by FFmpeg for professional video processing*