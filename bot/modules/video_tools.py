#!/usr/bin/env python3
"""
Video Tools Module for WZML-X Bot
Provides comprehensive video processing capabilities including:
- Video compression
- Format conversion  
- Video merging
- Thumbnail extraction
- Video information
- Subtitle extraction
- Audio extraction
- Video trimming
- Resolution changing
- Watermark addition
"""

import os
import asyncio
import subprocess
import json
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from aiofiles.os import path as aiopath, remove as aioremove
from time import time

from bot import DOWNLOAD_DIR, bot, config_dict, LOGGER
from bot.helper.ext_utils.bot_utils import (
    get_readable_file_size,
    get_readable_time,
    new_task,
    sync_to_async,
    arg_parser,
    is_url,
)
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage,
    deleteMessage,
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands


class VideoProcessor:
    """Main video processing class with FFmpeg integration"""
    
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"
    
    async def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.ffmpeg_path, "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def get_video_info(self, video_path):
        """Get detailed video information using ffprobe"""
        try:
            cmd = [
                self.ffprobe_path, "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", video_path
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return json.loads(stdout.decode())
            return None
        except Exception as e:
            LOGGER.error(f"Error getting video info: {e}")
            return None    
async def compress_video(self, input_path, output_path, quality="medium", progress_callback=None):
        """Compress video with different quality presets"""
        quality_settings = {
            "low": ["-crf", "28", "-preset", "fast"],
            "medium": ["-crf", "23", "-preset", "medium"],
            "high": ["-crf", "18", "-preset", "slow"],
            "ultra": ["-crf", "15", "-preset", "veryslow"]
        }
        
        settings = quality_settings.get(quality, quality_settings["medium"])
        
        cmd = [
            self.ffmpeg_path, "-i", input_path,
            "-c:v", "libx264", "-c:a", "aac",
            *settings, "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd, progress_callback)
    
    async def convert_format(self, input_path, output_path, target_format):
        """Convert video to different format"""
        format_codecs = {
            "mp4": ["-c:v", "libx264", "-c:a", "aac"],
            "mkv": ["-c:v", "libx264", "-c:a", "aac"],
            "avi": ["-c:v", "libxvid", "-c:a", "mp3"],
            "webm": ["-c:v", "libvpx-vp9", "-c:a", "libopus"],
            "mov": ["-c:v", "libx264", "-c:a", "aac"]
        }
        
        codecs = format_codecs.get(target_format.lower(), format_codecs["mp4"])
        
        cmd = [
            self.ffmpeg_path, "-i", input_path,
            *codecs, "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd)
    
    async def extract_thumbnail(self, video_path, output_path, timestamp="00:00:05"):
        """Extract thumbnail from video at specified timestamp"""
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-ss", timestamp, "-vframes", "1",
            "-q:v", "2", "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd)
    
    async def extract_audio(self, video_path, output_path, audio_format="mp3"):
        """Extract audio from video"""
        format_codecs = {
            "mp3": ["-c:a", "mp3", "-b:a", "192k"],
            "aac": ["-c:a", "aac", "-b:a", "128k"],
            "flac": ["-c:a", "flac"],
            "wav": ["-c:a", "pcm_s16le"]
        }
        
        codecs = format_codecs.get(audio_format.lower(), format_codecs["mp3"])
        
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-vn", *codecs, "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd)    asy
nc def trim_video(self, input_path, output_path, start_time, duration=None, end_time=None):
        """Trim video from start_time with duration or to end_time"""
        cmd = [self.ffmpeg_path, "-i", input_path, "-ss", start_time]
        
        if duration:
            cmd.extend(["-t", duration])
        elif end_time:
            cmd.extend(["-to", end_time])
        
        cmd.extend(["-c", "copy", "-y", output_path])
        
        return await self._run_ffmpeg_command(cmd)
    
    async def change_resolution(self, input_path, output_path, width, height, maintain_aspect=True):
        """Change video resolution"""
        if maintain_aspect:
            scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"
        else:
            scale_filter = f"scale={width}:{height}"
        
        cmd = [
            self.ffmpeg_path, "-i", input_path,
            "-vf", scale_filter,
            "-c:a", "copy", "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd)
    
    async def add_watermark(self, input_path, output_path, watermark_path, position="bottom-right"):
        """Add watermark to video"""
        positions = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2"
        }
        
        overlay_pos = positions.get(position, positions["bottom-right"])
        
        cmd = [
            self.ffmpeg_path, "-i", input_path, "-i", watermark_path,
            "-filter_complex", f"overlay={overlay_pos}",
            "-c:a", "copy", "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd)
    
    async def merge_videos(self, video_list, output_path):
        """Merge multiple videos into one"""
        # Create temporary file list
        list_file = f"{DOWNLOAD_DIR}/video_list.txt"
        with open(list_file, 'w') as f:
            for video in video_list:
                f.write(f"file '{video}'\n")
        
        cmd = [
            self.ffmpeg_path, "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", "-y", output_path
        ]
        
        result = await self._run_ffmpeg_command(cmd)
        
        # Clean up
        if await aiopath.exists(list_file):
            await aioremove(list_file)
        
        return result
    
    async def extract_subtitles(self, video_path, output_path):
        """Extract subtitles from video"""
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-map", "0:s:0", "-c:s", "srt", "-y", output_path
        ]
        
        return await self._run_ffmpeg_command(cmd)    as
ync def _run_ffmpeg_command(self, cmd, progress_callback=None):
        """Run FFmpeg command with optional progress tracking"""
        try:
            LOGGER.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, "Success"
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                LOGGER.error(f"FFmpeg error: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            LOGGER.error(f"Error running FFmpeg command: {e}")
            return False, str(e)


# Initialize video processor
video_processor = VideoProcessor()


# Command handlers
@new_task
async def video_info_handler(client, message):
    """Handle /vinfo command - Get video information"""
    if len(message.command) < 2:
        await sendMessage(message, "Usage: /vinfo <video_file_path_or_reply_to_video>")
        return
    
    # Check if FFmpeg is available
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    video_path = None
    
    # Check if replying to a video message
    if message.reply_to_message and message.reply_to_message.video:
        # Download the video first
        status_msg = await sendMessage(message, "📥 Downloading video...")
        try:
            video_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        except Exception as e:
            await editMessage(status_msg, f"❌ Error downloading video: {e}")
            return
    else:
        video_path = message.command[1]
        if not await aiopath.exists(video_path):
            await sendMessage(message, "❌ Video file not found")
            return
    
    # Get video information
    status_msg = await sendMessage(message, "🔍 Analyzing video...")
    
    info = await video_processor.get_video_info(video_path)
    if not info:
        await editMessage(status_msg, "❌ Failed to get video information")
        return
    
    # Format video information
    format_info = info.get('format', {})
    video_stream = None
    audio_stream = None
    
    for stream in info.get('streams', []):
        if stream.get('codec_type') == 'video' and not video_stream:
            video_stream = stream
        elif stream.get('codec_type') == 'audio' and not audio_stream:
            audio_stream = stream
    
    info_text = "📹 **Video Information**\n\n"
    info_text += f"**File:** `{os.path.basename(video_path)}`\n"
    info_text += f"**Size:** `{get_readable_file_size(int(format_info.get('size', 0)))}`\n"
    info_text += f"**Duration:** `{get_readable_time(float(format_info.get('duration', 0)))}`\n"
    info_text += f"**Format:** `{format_info.get('format_name', 'Unknown')}`\n\n"
    
    if video_stream:
        info_text += "**Video Stream:**\n"
        info_text += f"• Codec: `{video_stream.get('codec_name', 'Unknown')}`\n"
        info_text += f"• Resolution: `{video_stream.get('width', 'Unknown')}x{video_stream.get('height', 'Unknown')}`\n"
        info_text += f"• FPS: `{eval(video_stream.get('r_frame_rate', '0/1')):.2f}`\n"
        info_text += f"• Bitrate: `{int(video_stream.get('bit_rate', 0)) // 1000} kbps`\n\n"
    
    if audio_stream:
        info_text += "**Audio Stream:**\n"
        info_text += f"• Codec: `{audio_stream.get('codec_name', 'Unknown')}`\n"
        info_text += f"• Sample Rate: `{audio_stream.get('sample_rate', 'Unknown')} Hz`\n"
        info_text += f"• Channels: `{audio_stream.get('channels', 'Unknown')}`\n"
        info_text += f"• Bitrate: `{int(audio_stream.get('bit_rate', 0)) // 1000} kbps`\n"
    
    await editMessage(status_msg, info_text)
    
    # Clean up downloaded file if it was downloaded
    if message.reply_to_message and message.reply_to_message.video:
        if await aiopath.exists(video_path):
            await aioremove(video_path)@ne
w_task
async def compress_video_handler(client, message):
    """Handle /vcompress command - Compress video"""
    args = message.text.split()
    if len(args) < 2:
        help_text = """**Video Compression Usage:**
        
`/vcompress <quality> [reply_to_video]`

**Quality Options:**
• `low` - Fast compression, larger file size (CRF 28)
• `medium` - Balanced compression (CRF 23) [Default]
• `high` - Better quality, slower (CRF 18)
• `ultra` - Best quality, very slow (CRF 15)

**Example:** `/vcompress medium` (reply to a video)"""
        await sendMessage(message, help_text)
        return
    
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    quality = args[1].lower()
    if quality not in ["low", "medium", "high", "ultra"]:
        await sendMessage(message, "❌ Invalid quality. Use: low, medium, high, or ultra")
        return
    
    if not message.reply_to_message or not message.reply_to_message.video:
        await sendMessage(message, "❌ Please reply to a video file")
        return
    
    status_msg = await sendMessage(message, "📥 Downloading video...")
    
    try:
        # Download original video
        input_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        original_size = os.path.getsize(input_path)
        
        await editMessage(status_msg, f"🔄 Compressing video with {quality} quality...")
        
        # Compress video
        output_path = f"{input_path}_compressed.mp4"
        success, error_msg = await video_processor.compress_video(input_path, output_path, quality)
        
        if not success:
            await editMessage(status_msg, f"❌ Compression failed: {error_msg}")
            return
        
        if not await aiopath.exists(output_path):
            await editMessage(status_msg, "❌ Compressed file not found")
            return
        
        compressed_size = os.path.getsize(output_path)
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        
        await editMessage(status_msg, "📤 Uploading compressed video...")
        
        # Upload compressed video
        caption = f"🎬 **Video Compressed**\n\n"
        caption += f"**Quality:** `{quality.title()}`\n"
        caption += f"**Original Size:** `{get_readable_file_size(original_size)}`\n"
        caption += f"**Compressed Size:** `{get_readable_file_size(compressed_size)}`\n"
        caption += f"**Space Saved:** `{compression_ratio:.1f}%`"
        
        await client.send_video(
            chat_id=message.chat.id,
            video=output_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        await deleteMessage(status_msg)
        
    except Exception as e:
        await editMessage(status_msg, f"❌ Error: {e}")
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if await aiopath.exists(path):
                await aioremove(path)


@new_task
async def convert_video_handler(client, message):
    """Handle /vconvert command - Convert video format"""
    args = message.text.split()
    if len(args) < 2:
        help_text = """**Video Format Conversion Usage:**
        
`/vconvert <format> [reply_to_video]`

**Supported Formats:**
• `mp4` - H.264/AAC (Most compatible)
• `mkv` - H.264/AAC (High quality container)
• `avi` - XviD/MP3 (Legacy format)
• `webm` - VP9/Opus (Web optimized)
• `mov` - H.264/AAC (Apple format)

**Example:** `/vconvert mp4` (reply to a video)"""
        await sendMessage(message, help_text)
        return
    
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    target_format = args[1].lower()
    supported_formats = ["mp4", "mkv", "avi", "webm", "mov"]
    
    if target_format not in supported_formats:
        await sendMessage(message, f"❌ Unsupported format. Supported: {', '.join(supported_formats)}")
        return
    
    if not message.reply_to_message or not message.reply_to_message.video:
        await sendMessage(message, "❌ Please reply to a video file")
        return
    
    status_msg = await sendMessage(message, "📥 Downloading video...")
    
    try:
        # Download original video
        input_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        
        await editMessage(status_msg, f"🔄 Converting to {target_format.upper()}...")
        
        # Convert video
        output_path = f"{os.path.splitext(input_path)[0]}_converted.{target_format}"
        success, error_msg = await video_processor.convert_format(input_path, output_path, target_format)
        
        if not success:
            await editMessage(status_msg, f"❌ Conversion failed: {error_msg}")
            return
        
        if not await aiopath.exists(output_path):
            await editMessage(status_msg, "❌ Converted file not found")
            return
        
        await editMessage(status_msg, "📤 Uploading converted video...")
        
        # Upload converted video
        caption = f"🎬 **Video Converted**\n\n"
        caption += f"**Format:** `{target_format.upper()}`\n"
        caption += f"**Size:** `{get_readable_file_size(os.path.getsize(output_path))}`"
        
        await client.send_video(
            chat_id=message.chat.id,
            video=output_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        await deleteMessage(status_msg)
        
    except Exception as e:
        await editMessage(status_msg, f"❌ Error: {e}")
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if await aiopath.exists(path):
                await aioremove(path)@new_task

async def extract_thumbnail_handler(client, message):
    """Handle /vthumb command - Extract video thumbnail"""
    args = message.text.split()
    timestamp = "00:00:05"  # Default timestamp
    
    if len(args) > 1:
        timestamp = args[1]
    
    if not message.reply_to_message or not message.reply_to_message.video:
        help_text = """**Extract Video Thumbnail Usage:**
        
`/vthumb [timestamp] [reply_to_video]`

**Examples:**
• `/vthumb` - Extract at 5 seconds (default)
• `/vthumb 00:01:30` - Extract at 1 minute 30 seconds
• `/vthumb 120` - Extract at 120 seconds

**Time Formats:**
• `HH:MM:SS` (e.g., 00:01:30)
• `MM:SS` (e.g., 01:30)
• `seconds` (e.g., 90)"""
        await sendMessage(message, help_text)
        return
    
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    status_msg = await sendMessage(message, "📥 Downloading video...")
    
    try:
        # Download video
        input_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        
        await editMessage(status_msg, f"🖼️ Extracting thumbnail at {timestamp}...")
        
        # Extract thumbnail
        output_path = f"{os.path.splitext(input_path)[0]}_thumb.jpg"
        success, error_msg = await video_processor.extract_thumbnail(input_path, output_path, timestamp)
        
        if not success:
            await editMessage(status_msg, f"❌ Thumbnail extraction failed: {error_msg}")
            return
        
        if not await aiopath.exists(output_path):
            await editMessage(status_msg, "❌ Thumbnail file not found")
            return
        
        # Upload thumbnail
        caption = f"🖼️ **Video Thumbnail**\n\n**Timestamp:** `{timestamp}`"
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=output_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        await deleteMessage(status_msg)
        
    except Exception as e:
        await editMessage(status_msg, f"❌ Error: {e}")
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if await aiopath.exists(path):
                await aioremove(path)


@new_task
async def extract_audio_handler(client, message):
    """Handle /vaudio command - Extract audio from video"""
    args = message.text.split()
    audio_format = "mp3"  # Default format
    
    if len(args) > 1:
        audio_format = args[1].lower()
    
    if not message.reply_to_message or not message.reply_to_message.video:
        help_text = """**Extract Audio from Video Usage:**
        
`/vaudio [format] [reply_to_video]`

**Supported Audio Formats:**
• `mp3` - MP3 format (192 kbps) [Default]
• `aac` - AAC format (128 kbps)
• `flac` - FLAC lossless format
• `wav` - WAV uncompressed format

**Example:** `/vaudio mp3` (reply to a video)"""
        await sendMessage(message, help_text)
        return
    
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    supported_formats = ["mp3", "aac", "flac", "wav"]
    if audio_format not in supported_formats:
        await sendMessage(message, f"❌ Unsupported format. Supported: {', '.join(supported_formats)}")
        return
    
    status_msg = await sendMessage(message, "📥 Downloading video...")
    
    try:
        # Download video
        input_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        
        await editMessage(status_msg, f"🎵 Extracting audio as {audio_format.upper()}...")
        
        # Extract audio
        output_path = f"{os.path.splitext(input_path)[0]}_audio.{audio_format}"
        success, error_msg = await video_processor.extract_audio(input_path, output_path, audio_format)
        
        if not success:
            await editMessage(status_msg, f"❌ Audio extraction failed: {error_msg}")
            return
        
        if not await aiopath.exists(output_path):
            await editMessage(status_msg, "❌ Audio file not found")
            return
        
        await editMessage(status_msg, "📤 Uploading audio file...")
        
        # Upload audio
        caption = f"🎵 **Audio Extracted**\n\n"
        caption += f"**Format:** `{audio_format.upper()}`\n"
        caption += f"**Size:** `{get_readable_file_size(os.path.getsize(output_path))}`"
        
        await client.send_audio(
            chat_id=message.chat.id,
            audio=output_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        await deleteMessage(status_msg)
        
    except Exception as e:
        await editMessage(status_msg, f"❌ Error: {e}")
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if await aiopath.exists(path):
                await aioremove(path)@
new_task
async def trim_video_handler(client, message):
    """Handle /vtrim command - Trim video"""
    args = message.text.split()
    if len(args) < 2:
        help_text = """**Video Trimming Usage:**
        
`/vtrim <start_time> [duration_or_end_time] [reply_to_video]`

**Time Formats:**
• `HH:MM:SS` (e.g., 00:01:30)
• `MM:SS` (e.g., 01:30)
• `seconds` (e.g., 90)

**Examples:**
• `/vtrim 00:00:30` - Start from 30 seconds to end
• `/vtrim 00:00:30 00:01:00` - From 30s for 1 minute duration
• `/vtrim 30 60` - From 30 seconds for 60 seconds
• `/vtrim 00:01:00 00:02:30` - From 1:00 to 2:30

**Note:** Second parameter can be duration or end time"""
        await sendMessage(message, help_text)
        return
    
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    if not message.reply_to_message or not message.reply_to_message.video:
        await sendMessage(message, "❌ Please reply to a video file")
        return
    
    start_time = args[1]
    duration = args[2] if len(args) > 2 else None
    
    status_msg = await sendMessage(message, "📥 Downloading video...")
    
    try:
        # Download video
        input_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        
        trim_info = f"from {start_time}"
        if duration:
            trim_info += f" for {duration}"
        
        await editMessage(status_msg, f"✂️ Trimming video {trim_info}...")
        
        # Trim video
        output_path = f"{os.path.splitext(input_path)[0]}_trimmed.mp4"
        success, error_msg = await video_processor.trim_video(input_path, output_path, start_time, duration)
        
        if not success:
            await editMessage(status_msg, f"❌ Trimming failed: {error_msg}")
            return
        
        if not await aiopath.exists(output_path):
            await editMessage(status_msg, "❌ Trimmed file not found")
            return
        
        await editMessage(status_msg, "📤 Uploading trimmed video...")
        
        # Upload trimmed video
        caption = f"✂️ **Video Trimmed**\n\n"
        caption += f"**Start Time:** `{start_time}`\n"
        if duration:
            caption += f"**Duration:** `{duration}`\n"
        caption += f"**Size:** `{get_readable_file_size(os.path.getsize(output_path))}`"
        
        await client.send_video(
            chat_id=message.chat.id,
            video=output_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        await deleteMessage(status_msg)
        
    except Exception as e:
        await editMessage(status_msg, f"❌ Error: {e}")
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if await aiopath.exists(path):
                await aioremove(path)


@new_task
async def resize_video_handler(client, message):
    """Handle /vresize command - Change video resolution"""
    args = message.text.split()
    if len(args) < 2:
        help_text = """**Video Resolution Change Usage:**
        
`/vresize <resolution> [reply_to_video]`

**Common Resolutions:**
• `720p` or `1280x720` - HD
• `1080p` or `1920x1080` - Full HD
• `480p` or `854x480` - SD
• `360p` or `640x360` - Low quality
• `4k` or `3840x2160` - Ultra HD
• `custom` - `WIDTHxHEIGHT` (e.g., 1600x900)

**Examples:**
• `/vresize 720p` - Resize to 720p
• `/vresize 1280x720` - Custom resolution
• `/vresize 1080p` - Resize to 1080p

**Note:** Aspect ratio is maintained by default"""
        await sendMessage(message, help_text)
        return
    
    if not await video_processor.check_ffmpeg():
        await sendMessage(message, "❌ FFmpeg is not installed or not available in PATH")
        return
    
    if not message.reply_to_message or not message.reply_to_message.video:
        await sendMessage(message, "❌ Please reply to a video file")
        return
    
    resolution = args[1].lower()
    
    # Parse resolution
    resolution_map = {
        "360p": (640, 360),
        "480p": (854, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "4k": (3840, 2160)
    }
    
    if resolution in resolution_map:
        width, height = resolution_map[resolution]
    elif 'x' in resolution:
        try:
            width, height = map(int, resolution.split('x'))
        except ValueError:
            await sendMessage(message, "❌ Invalid resolution format. Use WIDTHxHEIGHT (e.g., 1280x720)")
            return
    else:
        await sendMessage(message, "❌ Invalid resolution. Use predefined (720p, 1080p) or custom (1280x720)")
        return
    
    status_msg = await sendMessage(message, "📥 Downloading video...")
    
    try:
        # Download video
        input_path = await message.reply_to_message.download(file_name=f"{DOWNLOAD_DIR}/")
        
        await editMessage(status_msg, f"📐 Resizing video to {width}x{height}...")
        
        # Resize video
        output_path = f"{os.path.splitext(input_path)[0]}_resized.mp4"
        success, error_msg = await video_processor.change_resolution(input_path, output_path, width, height)
        
        if not success:
            await editMessage(status_msg, f"❌ Resizing failed: {error_msg}")
            return
        
        if not await aiopath.exists(output_path):
            await editMessage(status_msg, "❌ Resized file not found")
            return
        
        await editMessage(status_msg, "📤 Uploading resized video...")
        
        # Upload resized video
        caption = f"📐 **Video Resized**\n\n"
        caption += f"**Resolution:** `{width}x{height}`\n"
        caption += f"**Size:** `{get_readable_file_size(os.path.getsize(output_path))}`"
        
        await client.send_video(
            chat_id=message.chat.id,
            video=output_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        await deleteMessage(status_msg)
        
    except Exception as e:
        await editMessage(status_msg, f"❌ Error: {e}")
    finally:
        # Clean up files
        for path in [input_path, output_path]:
            if await aiopath.exists(path):
                await aioremove(path)@
new_task
async def video_help_handler(client, message):
    """Handle /vhelp command - Show video tools help"""
    help_text = """🎬 **Video Tools Help**

**Available Commands:**

🔍 **Information & Analysis:**
• `/vinfo` - Get detailed video information
• `/vhelp` - Show this help message

🎞️ **Video Processing:**
• `/vcompress <quality>` - Compress video (low/medium/high/ultra)
• `/vconvert <format>` - Convert video format (mp4/mkv/avi/webm/mov)
• `/vtrim <start> [duration]` - Trim video
• `/vresize <resolution>` - Change video resolution

🎵 **Audio & Media Extraction:**
• `/vaudio [format]` - Extract audio (mp3/aac/flac/wav)
• `/vthumb [timestamp]` - Extract thumbnail image

**Usage Notes:**
• Reply to a video file when using these commands
• Most commands support various quality/format options
• Processing time depends on video size and complexity
• FFmpeg must be installed for video processing

**Examples:**
• `/vcompress medium` (reply to video)
• `/vconvert mp4` (reply to video)  
• `/vtrim 00:01:00 00:02:00` (reply to video)
• `/vresize 720p` (reply to video)

**Quality Guidelines:**
• **Low:** Fast processing, larger files
• **Medium:** Balanced quality and size
• **High:** Better quality, slower processing
• **Ultra:** Best quality, longest processing time

For detailed help on any command, use the command without parameters."""
    
    await sendMessage(message, help_text)


# Register command handlers
bot.add_handler(MessageHandler(video_info_handler, filters=command(BotCommands.VideoInfoCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(compress_video_handler, filters=command(BotCommands.CompressVideoCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(convert_video_handler, filters=command(BotCommands.ConvertVideoCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(extract_thumbnail_handler, filters=command(BotCommands.VideoThumbnailCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(extract_audio_handler, filters=command(BotCommands.ExtractAudioCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(trim_video_handler, filters=command(BotCommands.TrimVideoCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(resize_video_handler, filters=command(BotCommands.ResizeVideoCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(video_help_handler, filters=command(BotCommands.VideoHelpCommand) & CustomFilters.authorized))