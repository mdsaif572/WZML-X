from asyncio import sleep
from functools import partial
from html import escape
from io import BytesIO
from os import getcwd
from re import sub
from time import time

from aiofiles.os import makedirs, remove
from aiofiles.os import path as aiopath
from langcodes import Language
from pyrogram.filters import create
from pyrogram.handlers import MessageHandler

from bot.helper.ext_utils.status_utils import get_readable_file_size

from .. import auth_chats, excluded_extensions, sudo_users, user_data
from ..core.config_manager import Config
from ..core.tg_client import TgClient
from ..helper.ext_utils.bot_utils import (
    get_size_bytes,
    new_task,
    update_user_ldata,
)
from ..helper.ext_utils.db_handler import database
from ..helper.ext_utils.media_utils import create_thumb
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_file,
    send_message,
)

handler_dict = {}

leech_options = [
    "THUMBNAIL",
    "LEECH_SPLIT_SIZE",
    "LEECH_DUMP_CHAT",
    "LEECH_PREFIX",
    "LEECH_SUFFIX",
    "LEECH_CAPTION",
    "THUMBNAIL_LAYOUT",
]
rclone_options = ["RCLONE_CONFIG", "RCLONE_PATH", "RCLONE_FLAGS"]
gdrive_options = ["TOKEN_PICKLE", "GDRIVE_ID", "INDEX_URL"]
ffset_options = [
    "FFMPEG_CMDS",
    "METADATA",
    "AUDIO_METADATA",
    "VIDEO_METADATA",
    "SUBTITLE_METADATA",
]
advanced_options = [
    "EXCLUDED_EXTENSIONS",
    "NAME_SWAP",
    "YT_DLP_OPTIONS",
    "UPLOAD_PATHS",
    "USER_COOKIE_FILE",
]
yt_options = ["YT_DESP", "YT_TAGS", "YT_CATEGORY_ID", "YT_PRIVACY_STATUS"]

video_encode_options = [
    "VIDEO_ENCODE_PRESET",
    "VIDEO_ENCODE_QUALITY",
    "VIDEO_ENCODE_CRF",
    "VIDEO_ENCODE_AUDIO_BITRATE",
]

watermark_options = [
    "WATERMARK_TEXT",
    "WATERMARK_TYPE",
    "WATERMARK_IMAGE_PATH",
    "WATERMARK_POSITION",
    "WATERMARK_OPACITY",
    "WATERMARK_TEXT_BG",
    "WATERMARK_FONT",
    "WATERMARK_SIZE",
    "WATERMARK_COLOR",
    "WATERMARK_DURATION",
    "WATERMARK_SECONDS",
]

stream_options = [
    "KEEP_SOURCE",
    "STREAM_EXTRACT_OPTIONS",
    "STREAM_REMOVE_OPTIONS",
    "STREAM_SWAP_OPTIONS",
]

video_video_options = [
    "VIDEO_STREAM_1",
    "VIDEO_STREAM_2",
    "VIDEO_MERGE_OPTIONS",
    "VIDEO_OVERLAY_OPTIONS",
    "VIDEO_CONCAT_OPTIONS",
    "VIDEO_SPLIT_OPTIONS",
]

video_audio_options = [
    "AUDIO_TRACK_1",
    "AUDIO_TRACK_2",
    "AUDIO_MIX_OPTIONS",
    "AUDIO_REPLACE_OPTIONS",
    "AUDIO_SYNC_OPTIONS",
    "AUDIO_VOLUME_OPTIONS",
]

video_subtitle_options = [
    "SUBTITLE_FILE",
    "SUBTITLE_EMBED_OPTIONS",
    "SUBTITLE_BURN_OPTIONS",
    "SUBTITLE_STYLE_OPTIONS",
    "SUBTITLE_POSITION_OPTIONS",
    "SUBTITLE_LANGUAGE_OPTIONS",
]

rename_options = [
    "RENAME_PATTERN",
    "RENAME_PREFIX",
    "RENAME_SUFFIX",
    "RENAME_EXTENSION",
    "RENAME_CASE_OPTIONS",
    "RENAME_REPLACE_OPTIONS",
]

user_settings_text = {
    "THUMBNAIL": (
        "Photo or Doc",
        "Custom Thumbnail is used as the thumbnail for the files you upload to telegram in media or document mode.",
        "<i>Send a photo to save it as custom thumbnail.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RCLONE_CONFIG": (
        "",
        "",
        "<i>Send your <code>rclone.conf</code> file to use as your Upload Dest to RClone.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "TOKEN_PICKLE": (
        "",
        "",
        "<i>Send your <code>token.pickle</code> to use as your Upload Dest to GDrive</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_SPLIT_SIZE": (
        "",
        "",
        f"Send Leech split size in bytes or use gb or mb. Example: 40000000 or 2.5gb or 1000mb. PREMIUM_USER: {TgClient.IS_PREMIUM_USER}.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_DUMP_CHAT": (
        "",
        "",
        """Send leech destination ID/USERNAME/PM. 
* b:id/@username/pm (b: means leech by bot) (id or username of the chat or write pm means private message so bot will send the files in private to you) when you should use b:(leech by bot)? When your default settings is leech by user and you want to leech by bot for specific task.
* u:id/@username(u: means leech by user) This incase OWNER added USER_STRING_SESSION.
* h:id/@username(hybrid leech) h: to upload files by bot and user based on file size.
* id/@username|topic_id(leech in specific chat and topic) add | without space and write topic id after chat id or username.
┖ <b>Time Left :</b> <code>60 sec</code>""",
    ),
    "LEECH_PREFIX": (
        "",
        "",
        "Send Leech Filename Prefix. You can add HTML tags. Example: <code>@mychannel</code>.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_SUFFIX": (
        "",
        "",
        "Send Leech Filename Suffix. You can add HTML tags. Example: <code>@mychannel</code>.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_CAPTION": (
        "",
        "",
        "Send Leech Caption. You can add HTML tags. Example: <code>@mychannel</code>.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "THUMBNAIL_LAYOUT": (
        "",
        "",
        "Send thumbnail layout (widthxheight, 2x2, 3x3, 2x4, 4x4, ...). Example: 3x3.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RCLONE_PATH": (
        "",
        "",
        "Send Rclone Path. If you want to use your rclone config edit using owner/user config from usetting or add mrcc: before rclone path. Example mrcc:remote:folder. </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RCLONE_FLAGS": (
        "",
        "",
        "key:value|key|key|key:value . Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>\nEx: --buffer-size:8M|--drive-starred-only",
    ),
    "GDRIVE_ID": (
        "",
        "",
        "Send Gdrive ID. If you want to use your token.pickle edit using owner/user token from usetting or add mtp: before the id. Example: mtp:F435RGGRDXXXXXX . </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "INDEX_URL": (
        "",
        "",
        "Send Index URL for your gdrive option. </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "UPLOAD_PATHS": (
        "",
        "",
        "Send Dict of keys that have path values. Example: {'path 1': 'remote:rclonefolder', 'path 2': 'gdrive1 id', 'path 3': 'tg chat id', 'path 4': 'mrcc:remote:', 'path 5': b:@username} . </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "EXCLUDED_EXTENSIONS": (
        "",
        "",
        "Send exluded extenions seperated by space without dot at beginning. </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "NAME_SWAP": (
        "",
        "",
        """<i>Send your Name Swap. You can add pattern instead of normal text according to the format.</i>
<b>Full Documentation Guide</b> <a href="https://t.me/WZML_X/77">Click Here</a>
┖ <b>Time Left :</b> <code>60 sec</code>
""",
    ),
    "YT_DLP_OPTIONS": (
        "",
        "",
        """Format: {key: value, key: value, key: value}.
Example: {"format": "bv*+mergeall[vcodec=none]", "nocheckcertificate": True, "playliststart": 10, "fragment_retries": float("inf"), "matchtitle": "S13", "writesubtitles": True, "live_from_start": True, "postprocessor_args": {"ffmpeg": ["-threads", "4"]}, "wait_for_video": (5, 100), "download_ranges": [{"start_time": 0, "end_time": 10}]}
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.

<i>Send dict of YT-DLP Options according to format.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>""",
    ),
    "FFMPEG_CMDS": (
        "",
        "",
        """Dict of list values of ffmpeg commands. You can set multiple ffmpeg commands for all files before upload. Don't write ffmpeg at beginning, start directly with the arguments.
Examples: {"subtitle": ["-i mltb.mkv -c copy -c:s srt mltb.mkv", "-i mltb.video -c copy -c:s srt mltb"], "convert": ["-i mltb.m4a -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb.audio -c:a libmp3lame -q:a 2 mltb.mp3"], extract: ["-i mltb -map 0:a -c copy mltb.mka -map 0:s -c copy mltb.srt"]}
Notes:
- Add `-del` to the list which you want from the bot to delete the original files after command run complete!
- To execute one of those lists in bot for example, you must use -ff subtitle (list key) or -ff convert (list key)
Here I will explain how to use mltb.* which is reference to files you want to work on.
1. First cmd: the input is mltb.mkv so this cmd will work only on mkv videos and the output is mltb.mkv also so all outputs is mkv. -del will delete the original media after complete run of the cmd.
2. Second cmd: the input is mltb.video so this cmd will work on all videos and the output is only mltb so the extenstion is same as input files.
3. Third cmd: the input in mltb.m4a so this cmd will work only on m4a audios and the output is mltb.mp3 so the output extension is mp3.
4. Fourth cmd: the input is mltb.audio so this cmd will work on all audios and the output is mltb.mp3 so the output extension is mp3.

<i>Send dict of FFMPEG_CMDS Options according to format.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>
""",
    ),
    "METADATA_CMDS": (
        "",
        "",
        """<i>Send your Meta data. You can according to the format title="Join @WZML_X".</i>
<b>Full Documentation Guide</b> <a href="https://t.me/WZML_X/">Click Here</a>
┖ <b>Time Left :</b> <code>60 sec</code>
""",
    ),
    "METADATA": (
        "🏷 Global Metadata (key=value|key=value)",
        "Apply metadata to all media files with dynamic variables.",
        """<i>📝 Send metadata as</i> <code>key=value|key2=value2</code>

<b>🔧 Dynamic Variables:</b>
• <code>{filename}</code> - Original filename
• <code>{basename}</code> - Name without extension
• <code>{audiolang}</code> - Audio language (English/Hindi etc.)
• <code>{year}</code> - Year from filename

<b>📋 Example:</b>
<code>title={basename}|artist={audiolang} Version|year={year}</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "AUDIO_METADATA": (
        "🎵 Audio Stream Metadata",
        "Metadata applied to each audio track separately.",
        """<i>🎧 Audio stream metadata with per-track language support</i>

<b>📋 Example:</b>
<code>language={audiolang}|title=Audio - {audiolang}</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "VIDEO_METADATA": (
        "🎥 Video Stream Metadata",
        "Metadata applied to video streams.",
        """<i>📹 Video stream metadata for visual tracks</i>

<b>📋 Example:</b>
<code>title={basename}|comment=HD Video</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "SUBTITLE_METADATA": (
        "💬 Subtitle Stream Metadata",
        "Metadata applied to each subtitle track separately.",
        """<i>📄 Subtitle stream metadata with per-track language support</i>

<b>📋 Example:</b>
<code>language={sublang}|title=Subtitles - {sublang}</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "YT_DESP": (
        "String",
        "Custom description for YouTube uploads. Default is used if not set.",
        "<i>Send your custom YouTube description.</i> \nTime Left : <code>60 sec</code>",
    ),
    "YT_TAGS": (
        "Comma-separated strings",
        "Custom tags for YouTube uploads (e.g., tag1,tag2,tag3). Default is used if not set.",
        "<i>Send your custom YouTube tags as a comma-separated list.</i> \nTime Left : <code>60 sec</code>",
    ),
    "YT_CATEGORY_ID": (
        "Number",
        "Custom category ID for YouTube uploads. Default is used if not set.",
        "<i>Send your custom YouTube category ID (e.g., 22).</i> \nTime Left : <code>60 sec</code>",
    ),
    "YT_PRIVACY_STATUS": (
        "public, private, or unlisted",
        "Custom privacy status for YouTube uploads. Default is used if not set.",
        "<i>Send your custom YouTube privacy status (public, private, or unlisted).</i> \nTime Left : <code>60 sec</code>",
    ),
    "USER_COOKIE_FILE": (
        "File",
        "User's YT-DLP Cookie File to authenticate access to websites and youtube.",
        "<i>Send your cookie file (e.g., cookies.txt or abc.txt).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # Video Encoding Settings
    "VIDEO_ENCODE_PRESET": (
        "String",
        "Set the encoding preset for videos. Available options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow.",
        "<i>Send encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_ENCODE_QUALITY": (
        "String",
        "Set video resolution/quality. Options: 1080p, 720p, 576p, 480p, 360p, Original.",
        "<i>Send video quality (1080p, 720p, 576p, 480p, 360p, Original).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_ENCODE_CRF": (
        "Number",
        "Constant Rate Factor controls quality. Lower values = higher quality but larger files. Range: 0-51.",
        "<i>Send CRF value (18-30 recommended, 23 is default).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_ENCODE_AUDIO_BITRATE": (
        "String",
        "Audio bitrate determines sound quality. Higher values = better audio but larger files.",
        "<i>Send audio bitrate (64k, 96k, 128k, 192k, 256k, 320k).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # Watermark Settings
    "WATERMARK_TEXT": (
        "String",
        "Text to display as watermark on videos.",
        "<i>Send watermark text content.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_TYPE": (
        "String",
        "Type of watermark: text or image.",
        "<i>Send watermark type (text or image).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_IMAGE_PATH": (
        "File",
        "Image file to use as watermark.",
        "<i>Send image file for watermark.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_POSITION": (
        "String",
        "Position of watermark on video (top-left, top-right, bottom-left, bottom-right, center).",
        "<i>Send watermark position (top-left, top-right, bottom-left, bottom-right, center).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_OPACITY": (
        "Number",
        "Watermark transparency level (0.0 to 1.0, where 1.0 is fully opaque).",
        "<i>Send opacity value (0.0 to 1.0, e.g., 0.7).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_TEXT_BG": (
        "Boolean",
        "Enable background for text watermark.",
        "<i>Send true or false for text background.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_FONT": (
        "String",
        "Font family for text watermark.",
        "<i>Send font name (Arial, Times, Helvetica, etc.).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_SIZE": (
        "String",
        "Size of watermark (small, medium, large).",
        "<i>Send watermark size (small, medium, large).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_COLOR": (
        "String",
        "Color of watermark text in hex format.",
        "<i>Send color in hex format (e.g., #FFFFFF for white).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_DURATION": (
        "String",
        "Duration for watermark display (full, start, end, custom).",
        "<i>Send duration type (full, start, end, custom).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "WATERMARK_SECONDS": (
        "Number",
        "Specific timing in seconds for watermark display.",
        "<i>Send duration in seconds.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # Stream Processing Settings
    "KEEP_SOURCE": (
        "Boolean",
        "Keep original source files after processing.",
        "<i>Send true or false to keep source files.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "STREAM_EXTRACT_OPTIONS": (
        "Dict",
        "Options for extracting specific streams from media files.",
        "<i>Send dict of stream extraction options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "STREAM_REMOVE_OPTIONS": (
        "Dict",
        "Options for removing specific streams from media files.",
        "<i>Send dict of stream removal options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "STREAM_SWAP_OPTIONS": (
        "Dict",
        "Options for swapping/reordering streams in media files.",
        "<i>Send dict of stream swapping options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # Video + Video Processing Settings
    "VIDEO_STREAM_1": (
        "String",
        "Primary video input stream configuration.",
        "<i>Send video stream 1 configuration.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_STREAM_2": (
        "String",
        "Secondary video input stream configuration.",
        "<i>Send video stream 2 configuration.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_MERGE_OPTIONS": (
        "Dict",
        "Options for merging multiple video streams.",
        "<i>Send dict of video merge options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_OVERLAY_OPTIONS": (
        "Dict",
        "Options for overlaying one video on another.",
        "<i>Send dict of video overlay options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_CONCAT_OPTIONS": (
        "Dict",
        "Options for concatenating videos sequentially.",
        "<i>Send dict of video concatenation options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIDEO_SPLIT_OPTIONS": (
        "Dict",
        "Options for splitting video into segments.",
        "<i>Send dict of video split options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # Video + Audio Processing Settings
    "AUDIO_TRACK_1": (
        "String",
        "Primary audio track configuration.",
        "<i>Send audio track 1 configuration.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "AUDIO_TRACK_2": (
        "String",
        "Secondary audio track configuration.",
        "<i>Send audio track 2 configuration.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "AUDIO_MIX_OPTIONS": (
        "Dict",
        "Options for mixing multiple audio tracks.",
        "<i>Send dict of audio mix options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "AUDIO_REPLACE_OPTIONS": (
        "Dict",
        "Options for replacing video audio track.",
        "<i>Send dict of audio replacement options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "AUDIO_SYNC_OPTIONS": (
        "Dict",
        "Options for synchronizing audio with video.",
        "<i>Send dict of audio sync options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "AUDIO_VOLUME_OPTIONS": (
        "Dict",
        "Options for adjusting audio volume levels.",
        "<i>Send dict of audio volume options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # Video + Subtitle Processing Settings
    "SUBTITLE_FILE": (
        "File",
        "Subtitle file to embed or burn into video.",
        "<i>Send subtitle file (e.g., subtitles.srt).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SUBTITLE_EMBED_OPTIONS": (
        "Dict",
        "Options for embedding subtitles in video container.",
        "<i>Send dict of subtitle embed options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SUBTITLE_BURN_OPTIONS": (
        "Dict",
        "Options for burning subtitles permanently into video.",
        "<i>Send dict of subtitle burn options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SUBTITLE_STYLE_OPTIONS": (
        "Dict",
        "Options for configuring subtitle appearance and style.",
        "<i>Send dict of subtitle style options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SUBTITLE_POSITION_OPTIONS": (
        "Dict",
        "Options for setting subtitle position on screen.",
        "<i>Send dict of subtitle position options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SUBTITLE_LANGUAGE_OPTIONS": (
        "Dict",
        "Options for setting subtitle language metadata.",
        "<i>Send dict of subtitle language options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    # File Rename Settings
    "RENAME_PATTERN": (
        "String",
        "Pattern for renaming files with variables and placeholders.",
        "<i>Send rename pattern (e.g., {filename}_{date}).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RENAME_PREFIX": (
        "String",
        "Prefix to add to the beginning of filenames.",
        "<i>Send filename prefix.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RENAME_SUFFIX": (
        "String",
        "Suffix to add to the end of filenames (before extension).",
        "<i>Send filename suffix.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RENAME_EXTENSION": (
        "String",
        "New file extension to replace the original.",
        "<i>Send new file extension (e.g., mp4, mkv).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RENAME_CASE_OPTIONS": (
        "String",
        "Options for changing filename case (upper, lower, title).",
        "<i>Send case option (upper, lower, title).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RENAME_REPLACE_OPTIONS": (
        "Dict",
        "Options for finding and replacing text in filenames.",
        "<i>Send dict of find/replace options.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
}


async def get_user_settings(from_user, stype="main"):
    user_id = from_user.id
    user_name = from_user.mention(style="html")
    buttons = ButtonMaker()
    rclone_conf = f"rclone/{user_id}.conf"
    token_pickle = f"tokens/{user_id}.pickle"
    user_dict = user_data.get(user_id, {})

    if stype == "main":
        buttons.data_button(
            "General Settings", f"userset {user_id} general", position="header"
        )
        buttons.data_button("Mirror Settings", f"userset {user_id} mirror")
        buttons.data_button("Leech Settings", f"userset {user_id} leech")
        buttons.data_button("FF Media Settings", f"userset {user_id} ffset")
        buttons.data_button(
            "Mics Settings", f"userset {user_id} advanced", position="l_body"
        )

        if user_dict and any(
            key in user_dict
            for key in list(user_settings_text.keys())
            + [
                "USER_TOKENS",
                "AS_DOCUMENT",
                "EQUAL_SPLITS",
                "MEDIA_GROUP",
                "USER_TRANSMISSION",
                "HYBRID_LEECH",
                "STOP_DUPLICATE",
                "DEFAULT_UPLOAD",
            ]
        ):
            buttons.data_button(
                "Reset All", f"userset {user_id} confirm_reset_all", position="footer"
            )
        buttons.data_button("Close", f"userset {user_id} close", position="footer")

        text = f"""⌬ <b>User Settings :</b>
│
┟ <b>Name</b> → {user_name}
┠ <b>UserID</b> → #ID{user_id}
┠ <b>Username</b> → @{from_user.username}
┠ <b>Telegram DC</b> → {from_user.dc_id}
┖ <b>Telegram Lang</b> → {Language.get(lc).display_name() if (lc := from_user.language_code) else "N/A"}"""

        btns = buttons.build_menu(2)

    elif stype == "general":
        if user_dict.get("DEFAULT_UPLOAD", ""):
            default_upload = user_dict["DEFAULT_UPLOAD"]
        elif "DEFAULT_UPLOAD" not in user_dict:
            default_upload = Config.DEFAULT_UPLOAD
        du = "GDRIVE API" if default_upload == "gd" else "RCLONE"
        dur = "GDRIVE API" if default_upload != "gd" else "RCLONE"
        buttons.data_button(
            f"Swap to {dur} Mode", f"userset {user_id} {default_upload}"
        )

        user_tokens = user_dict.get("USER_TOKENS", False)
        tr = "USER" if user_tokens else "OWNER"
        trr = "OWNER" if user_tokens else "USER"
        buttons.data_button(
            f"Swap to {trr} token/config",
            f"userset {user_id} tog USER_TOKENS {'f' if user_tokens else 't'}",
        )

        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")

        def_cookies = user_dict.get("USE_DEFAULT_COOKIE", False)
        cookie_mode = "Owner's Cookie" if def_cookies else "User's Cookie"
        buttons.data_button(
            f"Swap to {'OWNER' if not def_cookies else 'USER'}'s Cookie File",
            f"userset {user_id} tog USE_DEFAULT_COOKIE {'f' if def_cookies else 't'}",
        )
        btns = buttons.build_menu(1)

        text = f"""⌬ <b>General Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Default Upload Package</b> → <b>{du}</b>
┠ <b>Default Usage Mode</b> → <b>{tr}'s</b> token/config
┖ <b>yt Cookies Mode</b> → <b>{cookie_mode}</b>
"""

    elif stype == "leech":
        thumbpath = f"thumbnails/{user_id}.jpg"
        buttons.data_button("Thumbnail", f"userset {user_id} menu THUMBNAIL")
        thumbmsg = "Exists" if await aiopath.exists(thumbpath) else "Not Exists"
        buttons.data_button(
            "Leech Split Size", f"userset {user_id} menu LEECH_SPLIT_SIZE"
        )
        if user_dict.get("LEECH_SPLIT_SIZE", False):
            split_size = user_dict["LEECH_SPLIT_SIZE"]
        else:
            split_size = Config.LEECH_SPLIT_SIZE
        buttons.data_button(
            "Leech Destination", f"userset {user_id} menu LEECH_DUMP_CHAT"
        )
        if user_dict.get("LEECH_DUMP_CHAT", False):
            leech_dest = user_dict["LEECH_DUMP_CHAT"]
        elif "LEECH_DUMP_CHAT" not in user_dict and Config.LEECH_DUMP_CHAT:
            leech_dest = Config.LEECH_DUMP_CHAT
        else:
            leech_dest = "None"
        buttons.data_button("Leech Prefix", f"userset {user_id} menu LEECH_PREFIX")
        if user_dict.get("LEECH_PREFIX", False):
            lprefix = user_dict["LEECH_PREFIX"]
        elif "LEECH_PREFIX" not in user_dict and Config.LEECH_PREFIX:
            lprefix = Config.LEECH_PREFIX
        else:
            lprefix = "Not Exists"
        buttons.data_button("Leech Suffix", f"userset {user_id} menu LEECH_SUFFIX")
        if user_dict.get("LEECH_SUFFIX", False):
            lsuffix = user_dict["LEECH_SUFFIX"]
        elif "LEECH_SUFFIX" not in user_dict and Config.LEECH_SUFFIX:
            lsuffix = Config.LEECH_SUFFIX
        else:
            lsuffix = "Not Exists"

        buttons.data_button("Leech Caption", f"userset {user_id} menu LEECH_CAPTION")
        if user_dict.get("LEECH_CAPTION", False):
            lcap = user_dict["LEECH_CAPTION"]
        elif "LEECH_CAPTION" not in user_dict and Config.LEECH_CAPTION:
            lcap = Config.LEECH_CAPTION
        else:
            lcap = "Not Exists"

        if (
            user_dict.get("AS_DOCUMENT", False)
            or "AS_DOCUMENT" not in user_dict
            and Config.AS_DOCUMENT
        ):
            ltype = "DOCUMENT"
            buttons.data_button("Send As Media", f"userset {user_id} tog AS_DOCUMENT f")
        else:
            ltype = "MEDIA"
            buttons.data_button(
                "Send As Document", f"userset {user_id} tog AS_DOCUMENT t"
            )
        if (
            user_dict.get("EQUAL_SPLITS", False)
            or "EQUAL_SPLITS" not in user_dict
            and Config.EQUAL_SPLITS
        ):
            buttons.data_button(
                "Disable Equal Splits", f"userset {user_id} tog EQUAL_SPLITS f"
            )
            equal_splits = "Enabled"
        else:
            buttons.data_button(
                "Enable Equal Splits", f"userset {user_id} tog EQUAL_SPLITS t"
            )
            equal_splits = "Disabled"
        if (
            user_dict.get("MEDIA_GROUP", False)
            or "MEDIA_GROUP" not in user_dict
            and Config.MEDIA_GROUP
        ):
            buttons.data_button(
                "Disable Media Group", f"userset {user_id} tog MEDIA_GROUP f"
            )
            media_group = "Enabled"
        else:
            buttons.data_button(
                "Enable Media Group", f"userset {user_id} tog MEDIA_GROUP t"
            )
            media_group = "Disabled"
        if (
            TgClient.IS_PREMIUM_USER
            and user_dict.get("USER_TRANSMISSION", False)
            or "USER_TRANSMISSION" not in user_dict
            and Config.USER_TRANSMISSION
        ):
            buttons.data_button(
                "Leech by Bot", f"userset {user_id} tog USER_TRANSMISSION f"
            )
            leech_method = "user"
        elif TgClient.IS_PREMIUM_USER:
            leech_method = "bot"
            buttons.data_button(
                "Leech by User", f"userset {user_id} tog USER_TRANSMISSION t"
            )
        else:
            leech_method = "bot"

        if (
            TgClient.IS_PREMIUM_USER
            and user_dict.get("HYBRID_LEECH", False)
            or "HYBRID_LEECH" not in user_dict
            and Config.HYBRID_LEECH
        ):
            hybrid_leech = "Enabled"
            buttons.data_button(
                "Disable Hybride Leech", f"userset {user_id} tog HYBRID_LEECH f"
            )
        elif TgClient.IS_PREMIUM_USER:
            hybrid_leech = "Disabled"
            buttons.data_button(
                "Enable HYBRID Leech", f"userset {user_id} tog HYBRID_LEECH t"
            )
        else:
            hybrid_leech = "Disabled"

        buttons.data_button(
            "Thumbnail Layout", f"userset {user_id} menu THUMBNAIL_LAYOUT"
        )
        if user_dict.get("THUMBNAIL_LAYOUT", False):
            thumb_layout = user_dict["THUMBNAIL_LAYOUT"]
        elif "THUMBNAIL_LAYOUT" not in user_dict and Config.THUMBNAIL_LAYOUT:
            thumb_layout = Config.THUMBNAIL_LAYOUT
        else:
            thumb_layout = "None"

        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Leech Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ Leech Type → <b>{ltype}</b>
┠ Custom Thumbnail → <b>{thumbmsg}</b>
┠ Leech Split Size → <b>{get_readable_file_size(split_size)}</b>
┠ Equal Splits → <b>{equal_splits}</b>
┠ Media Group → <b>{media_group}</b>
┠ Leech Prefix → <code>{escape(lprefix)}</code>
┠ Leech Suffix → <code>{escape(lsuffix)}</code>
┠ Leech Caption → <code>{escape(lcap)}</code>
┠ Leech Destination → <code>{leech_dest}</code>
┠ Leech by <b>{leech_method}</b> session
┠ Mixed Leech → <b>{hybrid_leech}</b>
┖ Thumbnail Layout → <b>{thumb_layout}</b>
"""

    elif stype == "rclone":
        buttons.data_button("Rclone Config", f"userset {user_id} menu RCLONE_CONFIG")
        buttons.data_button(
            "Default Rclone Path", f"userset {user_id} menu RCLONE_PATH"
        )
        buttons.data_button("Rclone Flags", f"userset {user_id} menu RCLONE_FLAGS")

        buttons.data_button("Back", f"userset {user_id} back mirror", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")

        rccmsg = "Exists" if await aiopath.exists(rclone_conf) else "Not Exists"
        if user_dict.get("RCLONE_PATH", False):
            rccpath = user_dict["RCLONE_PATH"]
        elif Config.RCLONE_PATH:
            rccpath = Config.RCLONE_PATH
        else:
            rccpath = "None"
        btns = buttons.build_menu(1)

        if user_dict.get("RCLONE_FLAGS", False):
            rcflags = user_dict["RCLONE_FLAGS"]
        elif "RCLONE_FLAGS" not in user_dict and Config.RCLONE_FLAGS:
            rcflags = Config.RCLONE_FLAGS
        else:
            rcflags = "None"

        text = f"""⌬ <b>RClone Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Rclone Config</b> → <b>{rccmsg}</b>
┠ <b>Rclone Flags</b> → <code>{rcflags}</code>
┖ <b>Rclone Path</b> → <code>{rccpath}</code>"""

    elif stype == "gdrive":
        buttons.data_button("token.pickle", f"userset {user_id} menu TOKEN_PICKLE")
        buttons.data_button("Default Gdrive ID", f"userset {user_id} menu GDRIVE_ID")
        buttons.data_button("Index URL", f"userset {user_id} menu INDEX_URL")
        if (
            user_dict.get("STOP_DUPLICATE", False)
            or "STOP_DUPLICATE" not in user_dict
            and Config.STOP_DUPLICATE
        ):
            buttons.data_button(
                "Disable Stop Duplicate", f"userset {user_id} tog STOP_DUPLICATE f"
            )
            sd_msg = "Enabled"
        else:
            buttons.data_button(
                "Enable Stop Duplicate",
                f"userset {user_id} tog STOP_DUPLICATE t",
                "l_body",
            )
            sd_msg = "Disabled"
        buttons.data_button("Back", f"userset {user_id} back mirror", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")

        tokenmsg = "Exists" if await aiopath.exists(token_pickle) else "Not Exists"
        if user_dict.get("GDRIVE_ID", False):
            gdrive_id = user_dict["GDRIVE_ID"]
        elif GDID := Config.GDRIVE_ID:
            gdrive_id = GDID
        else:
            gdrive_id = "None"
        index = user_dict["INDEX_URL"] if user_dict.get("INDEX_URL", False) else "None"
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>GDrive Tools Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Gdrive Token</b> → <b>{tokenmsg}</b>
┠ <b>Gdrive ID</b> → <code>{gdrive_id}</code>
┠ <b>Index URL</b> → <code>{index}</code>
┖ <b>Stop Duplicate</b> → <b>{sd_msg}</b>"""
    elif stype == "mirror":
        buttons.data_button("RClone Tools", f"userset {user_id} rclone")
        rccmsg = "Exists" if await aiopath.exists(rclone_conf) else "Not Exists"
        if user_dict.get("RCLONE_PATH", False):
            rccpath = user_dict["RCLONE_PATH"]
        elif RP := Config.RCLONE_PATH:
            rccpath = RP
        else:
            rccpath = "None"

        buttons.data_button("GDrive Tools", f"userset {user_id} gdrive")
        tokenmsg = "Exists" if await aiopath.exists(token_pickle) else "Not Exists"
        if user_dict.get("GDRIVE_ID", False):
            gdrive_id = user_dict["GDRIVE_ID"]
        elif GI := Config.GDRIVE_ID:
            gdrive_id = GI
        else:
            gdrive_id = "None"

        index = user_dict["INDEX_URL"] if user_dict.get("INDEX_URL", False) else "None"
        if (
            user_dict.get("STOP_DUPLICATE", False)
            or "STOP_DUPLICATE" not in user_dict
            and Config.STOP_DUPLICATE
        ):
            sd_msg = "Enabled"
        else:
            sd_msg = "Disabled"

        buttons.data_button("YT Up Tools", f"userset {user_id} yttools")
        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(1)

        text = f"""⌬ <b>Mirror Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Rclone Config</b> → <b>{rccmsg}</b>
┠ <b>Rclone Path</b> → <code>{rccpath}</code>
┠ <b>Gdrive Token</b> → <b>{tokenmsg}</b>
┠ <b>Gdrive ID</b> → <code>{gdrive_id}</code>
┠ <b>Index Link</b> → <code>{index}</code>
┖ <b>Stop Duplicate</b> → <b>{sd_msg}</b>
"""

    elif stype == "ffset":
        buttons.data_button(
            "FFmpeg Cmds", f"userset {user_id} menu FFMPEG_CMDS", "header"
        )
        if user_dict.get("FFMPEG_CMDS", False):
            ffc = user_dict["FFMPEG_CMDS"]
        elif "FFMPEG_CMDS" not in user_dict and Config.FFMPEG_CMDS:
            ffc = Config.FFMPEG_CMDS
        else:
            ffc = "<b>Not Exists</b>"

        if isinstance(ffc, dict):
            ffc = "\n" + "\n".join(
                [
                    f"{no}. <b>{key}</b>: <code>{escape(str(value[0]))}</code>"
                    for no, (key, value) in enumerate(ffc.items(), start=1)
                ]
            )

        buttons.data_button("Metadata", f"userset {user_id} menu METADATA")
        metadata_setting = user_dict.get("METADATA")
        display_meta_val = "<b>Not Set</b>"
        if isinstance(metadata_setting, dict) and metadata_setting:
            display_meta_val = ", ".join(
                f"{k}={escape(str(v))}" for k, v in metadata_setting.items()
            )
            display_meta_val = f"<code>{display_meta_val}</code>"
        elif isinstance(metadata_setting, str) and metadata_setting:  # Legacy
            display_meta_val = (
                f"<code>{escape(metadata_setting)}</code> [<i>Legacy, needs re-set</i>]"
            )

        buttons.data_button("Audio Metadata", f"userset {user_id} menu AUDIO_METADATA")
        audio_meta_setting = user_dict.get("AUDIO_METADATA")
        display_audio_meta = "<b>Not Set</b>"
        if isinstance(audio_meta_setting, dict) and audio_meta_setting:
            display_audio_meta = ", ".join(
                f"{k}={escape(str(v))}" for k, v in audio_meta_setting.items()
            )
            display_audio_meta = f"<code>{display_audio_meta}</code>"

        buttons.data_button("Video Metadata", f"userset {user_id} menu VIDEO_METADATA")
        video_meta_setting = user_dict.get("VIDEO_METADATA")
        display_video_meta = "<b>Not Set</b>"
        if isinstance(video_meta_setting, dict) and video_meta_setting:
            display_video_meta = ", ".join(
                f"{k}={escape(str(v))}" for k, v in video_meta_setting.items()
            )
            display_video_meta = f"<code>{display_video_meta}</code>"

        buttons.data_button(
            "Subtitle Metadata", f"userset {user_id} menu SUBTITLE_METADATA"
        )
        subtitle_meta_setting = user_dict.get("SUBTITLE_METADATA")
        display_subtitle_meta = "<b>Not Set</b>"
        if isinstance(subtitle_meta_setting, dict) and subtitle_meta_setting:
            display_subtitle_meta = ", ".join(
                f"{k}={escape(str(v))}" for k, v in subtitle_meta_setting.items()
            )
            display_subtitle_meta = f"<code>{display_subtitle_meta}</code>"

        buttons.data_button("Video Encode", f"userset {user_id} video_encode")
        
        # Main Video Processing Menu button
        buttons.data_button("Video Processing", f"userset {user_id} video_processing")

        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>FF Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>FFmpeg CLI Commands</b> → {ffc}
┃
┠ <b>Default Metadata</b> → {display_meta_val}
┠ <b>Audio Metadata</b> → {display_audio_meta}
┠ <b>Video Metadata</b> → {display_video_meta}
┖ <b>Subtitle Metadata</b> → {display_subtitle_meta}"""

    elif stype == "advanced":
        buttons.data_button(
            "Excluded Extensions", f"userset {user_id} menu EXCLUDED_EXTENSIONS"
        )
        if user_dict.get("EXCLUDED_EXTENSIONS", False):
            ex_ex = user_dict["EXCLUDED_EXTENSIONS"]
        elif "EXCLUDED_EXTENSIONS" not in user_dict:
            ex_ex = excluded_extensions
        else:
            ex_ex = "None"

        if ex_ex != "None":
            ex_ex = ", ".join(ex_ex)

        ns_msg = (
            f"<code>{swap}</code>"
            if (swap := user_dict.get("NAME_SWAP", False))
            else "<b>Not Exists</b>"
        )
        buttons.data_button("Name Swap", f"userset {user_id} menu NAME_SWAP")

        buttons.data_button("YT-DLP Options", f"userset {user_id} menu YT_DLP_OPTIONS")
        if user_dict.get("YT_DLP_OPTIONS", False):
            ytopt = user_dict["YT_DLP_OPTIONS"]
        elif "YT_DLP_OPTIONS" not in user_dict and Config.YT_DLP_OPTIONS:
            ytopt = Config.YT_DLP_OPTIONS
        else:
            ytopt = "None"

        upload_paths = user_dict.get("UPLOAD_PATHS", {})
        if not upload_paths and "UPLOAD_PATHS" not in user_dict and Config.UPLOAD_PATHS:
            upload_paths = Config.UPLOAD_PATHS
        else:
            upload_paths = "None"
        buttons.data_button("Upload Paths", f"userset {user_id} menu UPLOAD_PATHS")

        yt_cookie_path = f"cookies/{user_id}/cookies.txt"
        user_cookie_msg = (
            "Exists" if await aiopath.exists(yt_cookie_path) else "Not Exists"
        )
        buttons.data_button(
            "YT Cookie File", f"userset {user_id} menu USER_COOKIE_FILE"
        )

        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(1)

        text = f"""⌬ <b>Advanced Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Name Swaps</b> → {ns_msg}
┠ <b>Excluded Extensions</b> → <code>{ex_ex}</code>
┠ <b>Upload Paths</b> → <b>{upload_paths}</b>
┠ <b>YT-DLP Options</b> → <code>{ytopt}</code>
┖ <b>YT User Cookie File</b> → <b>{user_cookie_msg}</b>"""
    elif stype == "video_encode":
        buttons.data_button("Preset", f"userset {user_id} video_preset")
        current_preset = user_dict.get("VIDEO_ENCODE_PRESET", "medium")
        
        buttons.data_button("Quality", f"userset {user_id} video_quality")
        current_quality = user_dict.get("VIDEO_ENCODE_QUALITY", "Original")
        
        buttons.data_button("CRF", f"userset {user_id} video_crf")
        current_crf = user_dict.get("VIDEO_ENCODE_CRF", 23)
        
        buttons.data_button("Audio Bitrate", f"userset {user_id} audio_bitrate")
        current_audio_bitrate = user_dict.get("VIDEO_ENCODE_AUDIO_BITRATE", "128k")

        buttons.data_button("Back", f"userset {user_id} ffset", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Video Encode Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Preset</b> → <code>{current_preset}</code>
┠ <b>Quality</b> → <code>{current_quality}</code>
┠ <b>CRF</b> → <code>{current_crf}</code>
┖ <b>Audio Bitrate</b> → <code>{current_audio_bitrate}</code>"""

    elif stype == "video_quality":
        current_quality = user_dict.get("VIDEO_ENCODE_QUALITY", "Original")
        
        # Quality option buttons
        quality_options = [
            ("1080p", "1080p"),
            ("720p", "720p"),
            ("576p", "576p"),
            ("480p", "480p"),
            ("360p", "360p"),
            ("Original", "Original")
        ]
        
        for quality_text, quality_value in quality_options:
            button_text = f"✓ {quality_text}" if current_quality == quality_value else quality_text
            buttons.data_button(button_text, f"userset {user_id} set_quality {quality_value}")

        buttons.data_button("Back", f"userset {user_id} video_encode", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Video Encoding Quality :</b>
┟ <b>Current Quality</b> → <code>{current_quality}</code>
┃
┠ <b>1080p</b> → Full HD, high quality (bitrate ~2000-2500k)
┠ <b>720p</b> → HD, balanced quality (bitrate ~1000-1500k)
┠ <b>576p</b> → PAL DVD quality (bitrate ~800-1000k)
┠ <b>480p</b> → DVD quality, medium size (bitrate ~500-800k)
┠ <b>360p</b> → Low resolution, small size (bitrate ~300-400k)
┖ <b>Original</b> → Keep original resolution, only apply preset"""

    elif stype == "video_crf":
        current_crf = user_dict.get("VIDEO_ENCODE_CRF", 23)
        
        # CRF option buttons
        crf_options = [
            (18, "18"),
            (20, "20"),
            (23, "23"),
            (25, "25"),
            (28, "28"),
            (30, "30")
        ]
        
        for crf_value, crf_text in crf_options:
            button_text = f"✓ {crf_text}" if current_crf == crf_value else crf_text
            buttons.data_button(button_text, f"userset {user_id} set_crf {crf_value}")

        buttons.data_button("Back", f"userset {user_id} video_encode", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(3)

        text = f"""⌬ <b>Video Encoding CRF :</b>
┟ <b>Current CRF</b> → <code>{current_crf}</code>
┃
┠ <b>What is CRF?</b>
┠ CRF (Constant Rate Factor) controls quality.
┠ Lower values = higher quality but larger files.
┠ Higher values = smaller files but lower quality.
┃
┠ <b>18</b> → Very high quality (visually lossless)
┠ <b>20</b> → High quality
┠ <b>23</b> → Default, good quality
┠ <b>25</b> → Standard quality, smaller size
┠ <b>28</b> → Lower quality, small size
┖ <b>30</b> → Low quality, very small size"""

    elif stype == "audio_bitrate":
        current_bitrate = user_dict.get("VIDEO_ENCODE_AUDIO_BITRATE", "128k")
        
        # Audio bitrate option buttons
        bitrate_options = [
            ("64k", "64k"),
            ("96k", "96k"),
            ("128k", "128k"),
            ("192k", "192k"),
            ("256k", "256k"),
            ("320k", "320k")
        ]
        
        for bitrate_value, bitrate_text in bitrate_options:
            button_text = f"✓ {bitrate_text}" if current_bitrate == bitrate_value else bitrate_text
            buttons.data_button(button_text, f"userset {user_id} set_audio_bitrate {bitrate_value}")

        buttons.data_button("Back", f"userset {user_id} video_encode", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(3)

        text = f"""⌬ <b>Audio Bitrate for Encoding :</b>
┟ <b>Current Bitrate</b> → <code>{current_bitrate}</code>
┃
┠ <b>What is Audio Bitrate?</b>
┠ Audio bitrate determines sound quality.
┠ Higher values = better audio but larger files.
┃
┠ <b>64k</b> → Low quality, smallest size
┠ <b>96k</b> → Basic quality, very small size
┠ <b>128k</b> → Standard quality (default)
┠ <b>192k</b> → Good quality, balanced size
┠ <b>256k</b> → Very good quality
┖ <b>320k</b> → Excellent quality, largest size"""

    elif stype == "video_preset":
        current_preset = user_dict.get("VIDEO_ENCODE_PRESET", "medium")
        
        # Preset option buttons
        preset_options = [
            ("ultrafast", "ultrafast"),
            ("superfast", "superfast"),
            ("veryfast", "veryfast"),
            ("faster", "faster"),
            ("fast", "fast"),
            ("medium", "medium"),
            ("slow", "slow"),
            ("slower", "slower"),
            ("veryslow", "veryslow")
        ]
        
        for preset_value, preset_text in preset_options:
            button_text = f"✓ {preset_text}" if current_preset == preset_value else preset_text
            buttons.data_button(button_text, f"userset {user_id} set_preset {preset_value}")

        buttons.data_button("Back", f"userset {user_id} video_encode", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(3)

        text = f"""⌬ <b>Video Encoding Preset :</b>
┟ <b>Current Preset</b> → <code>{current_preset}</code>
┃
┠ <b>Description</b> → Set the encoding preset for videos.
┠ Available options: ultrafast, superfast, veryfast,
┠ faster, fast, medium, slow, slower, veryslow.
┃
┠ <b>Speed vs Quality Trade-off:</b>
┠ • Faster presets = quicker encoding, larger files
┖ • Slower presets = better compression, smaller files"""

    elif stype == "video_processing":
        buttons.data_button("FFMPEG CMD", f"userset {user_id} menu FFMPEG_CMDS")
        buttons.data_button("MegaMetaData", f"userset {user_id} menu METADATA")
        
        buttons.data_button("Video + Video", f"userset {user_id} video_video")
        
        buttons.data_button("Video + Audio", f"userset {user_id} video_audio")
        buttons.data_button("Video + Subtitle", f"userset {user_id} video_subtitle")
        
        buttons.data_button("Stream Swap-Wap", f"userset {user_id} menu STREAM_SWAP_OPTIONS")
        
        buttons.data_button("Stream Extract", f"userset {user_id} menu STREAM_EXTRACT_OPTIONS")
        buttons.data_button("Stream Rem", f"userset {user_id} menu STREAM_REMOVE_OPTIONS")
        
        buttons.data_button("Video Encode", f"userset {user_id} video_encode")
        
        buttons.data_button("Watermark", f"userset {user_id} watermark")
        
        buttons.data_button("Keep Source", f"userset {user_id} menu KEEP_SOURCE")
        
        buttons.data_button("Rename", f"userset {user_id} rename")

        buttons.data_button("Back", f"userset {user_id} ffset", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Video Processing Menu :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>FFMPEG CMD</b> → Custom FFMPEG commands
┠ <b>MegaMetaData</b> → Global metadata settings
┠ <b>Video + Video</b> → Video stream processing
┠ <b>Video + Audio</b> → Audio stream processing
┠ <b>Video + Subtitle</b> → Subtitle processing
┠ <b>Stream Swap-Wap</b> → Stream reordering
┠ <b>Stream Extract</b> → Extract specific streams
┠ <b>Stream Rem</b> → Remove streams
┠ <b>Video Encode</b> → Video encoding settings
┠ <b>Watermark</b> → Watermark configuration
┠ <b>Keep Source</b> → Preserve original files
┖ <b>Rename</b> → File renaming options"""

    elif stype == "watermark":
        buttons.data_button("Set Text", f"userset {user_id} menu WATERMARK_TEXT")
        buttons.data_button("WM-Type", f"userset {user_id} menu WATERMARK_TYPE")
        buttons.data_button("Set Image", f"userset {user_id} menu WATERMARK_IMAGE_PATH")
        
        buttons.data_button("Position", f"userset {user_id} menu WATERMARK_POSITION")
        buttons.data_button("Opacity", f"userset {user_id} menu WATERMARK_OPACITY")
        buttons.data_button("Text-BG", f"userset {user_id} menu WATERMARK_TEXT_BG")
        
        buttons.data_button("Custom-Fo", f"userset {user_id} menu WATERMARK_FONT")
        buttons.data_button("Size", f"userset {user_id} menu WATERMARK_SIZE")
        buttons.data_button("Colour", f"userset {user_id} menu WATERMARK_COLOR")
        
        buttons.data_button("WM-Duration", f"userset {user_id} menu WATERMARK_DURATION")
        buttons.data_button("WM-Seconds", f"userset {user_id} menu WATERMARK_SECONDS")

        buttons.data_button("Back", f"userset {user_id} video_processing", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(3)

        # Get current watermark settings
        wm_text = user_dict.get("WATERMARK_TEXT", "Not Set")
        wm_type = user_dict.get("WATERMARK_TYPE", "text")
        wm_position = user_dict.get("WATERMARK_POSITION", "bottom-right")
        wm_opacity = user_dict.get("WATERMARK_OPACITY", 0.7)
        wm_size = user_dict.get("WATERMARK_SIZE", "medium")
        wm_color = user_dict.get("WATERMARK_COLOR", "#FFFFFF")

        text = f"""⌬ <b>Watermark Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Text</b> → <code>{escape(str(wm_text))}</code>
┠ <b>Type</b> → <code>{wm_type}</code>
┠ <b>Position</b> → <code>{wm_position}</code>
┠ <b>Opacity</b> → <code>{wm_opacity}</code>
┠ <b>Size</b> → <code>{wm_size}</code>
┖ <b>Color</b> → <code>{wm_color}</code>"""

    elif stype == "yttools":
        buttons.data_button("YT Description", f"userset {user_id} menu YT_DESP")
        yt_desp_val = user_dict.get(
            "YT_DESP",
            Config.YT_DESP if hasattr(Config, "YT_DESP") else "Not Set (Uses Default)",
        )

        buttons.data_button("YT Tags", f"userset {user_id} menu YT_TAGS")
        yt_tags_val = user_dict.get(
            "YT_TAGS",
            Config.YT_TAGS if hasattr(Config, "YT_TAGS") else "Not Set (Uses Default)",
        )
        if isinstance(yt_tags_val, list):
            yt_tags_val = ",".join(yt_tags_val)

        buttons.data_button("YT Category ID", f"userset {user_id} menu YT_CATEGORY_ID")
        yt_cat_id_val = user_dict.get(
            "YT_CATEGORY_ID",
            (
                Config.YT_CATEGORY_ID
                if hasattr(Config, "YT_CATEGORY_ID")
                else "Not Set (Uses Default)"
            ),
        )

        buttons.data_button(
            "YT Privacy Status", f"userset {user_id} menu YT_PRIVACY_STATUS"
        )
        yt_privacy_val = user_dict.get(
            "YT_PRIVACY_STATUS",
            (
                Config.YT_PRIVACY_STATUS
                if hasattr(Config, "YT_PRIVACY_STATUS")
                else "Not Set (Uses Default)"
            ),
        )

        buttons.data_button("Back", f"userset {user_id} back mirror", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>YouTube Tools Settings:</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>YT Description</b> → <code>{escape(str(yt_desp_val))}</code>
┠ <b>YT Tags</b> → <code>{escape(str(yt_tags_val))}</code>
┠ <b>YT Category ID</b> → <code>{escape(str(yt_cat_id_val))}</code>
┖ <b>YT Privacy Status</b> → <code>{escape(str(yt_privacy_val))}</code>"""

    elif stype == "video_video":
        buttons.data_button("Video Stream 1", f"userset {user_id} menu VIDEO_STREAM_1")
        buttons.data_button("Video Stream 2", f"userset {user_id} menu VIDEO_STREAM_2")
        buttons.data_button("Video Merge", f"userset {user_id} menu VIDEO_MERGE_OPTIONS")
        
        buttons.data_button("Video Overlay", f"userset {user_id} menu VIDEO_OVERLAY_OPTIONS")
        buttons.data_button("Video Concat", f"userset {user_id} menu VIDEO_CONCAT_OPTIONS")
        buttons.data_button("Video Split", f"userset {user_id} menu VIDEO_SPLIT_OPTIONS")

        buttons.data_button("Back", f"userset {user_id} video_processing", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Video + Video Processing :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Video Stream 1</b> → Primary video input
┠ <b>Video Stream 2</b> → Secondary video input
┠ <b>Video Merge</b> → Combine multiple videos
┠ <b>Video Overlay</b> → Overlay one video on another
┠ <b>Video Concat</b> → Concatenate videos sequentially
┖ <b>Video Split</b> → Split video into segments"""

    elif stype == "video_audio":
        buttons.data_button("Audio Track 1", f"userset {user_id} menu AUDIO_TRACK_1")
        buttons.data_button("Audio Track 2", f"userset {user_id} menu AUDIO_TRACK_2")
        buttons.data_button("Audio Mix", f"userset {user_id} menu AUDIO_MIX_OPTIONS")
        
        buttons.data_button("Audio Replace", f"userset {user_id} menu AUDIO_REPLACE_OPTIONS")
        buttons.data_button("Audio Sync", f"userset {user_id} menu AUDIO_SYNC_OPTIONS")
        buttons.data_button("Audio Volume", f"userset {user_id} menu AUDIO_VOLUME_OPTIONS")

        buttons.data_button("Back", f"userset {user_id} video_processing", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Video + Audio Processing :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Audio Track 1</b> → Primary audio input
┠ <b>Audio Track 2</b> → Secondary audio input
┠ <b>Audio Mix</b> → Mix multiple audio tracks
┠ <b>Audio Replace</b> → Replace video audio
┠ <b>Audio Sync</b> → Synchronize audio with video
┖ <b>Audio Volume</b> → Adjust audio levels"""

    elif stype == "video_subtitle":
        buttons.data_button("Subtitle File", f"userset {user_id} menu SUBTITLE_FILE")
        buttons.data_button("Subtitle Embed", f"userset {user_id} menu SUBTITLE_EMBED_OPTIONS")
        buttons.data_button("Subtitle Burn", f"userset {user_id} menu SUBTITLE_BURN_OPTIONS")
        
        buttons.data_button("Subtitle Style", f"userset {user_id} menu SUBTITLE_STYLE_OPTIONS")
        buttons.data_button("Subtitle Position", f"userset {user_id} menu SUBTITLE_POSITION_OPTIONS")
        buttons.data_button("Subtitle Language", f"userset {user_id} menu SUBTITLE_LANGUAGE_OPTIONS")

        buttons.data_button("Back", f"userset {user_id} video_processing", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Video + Subtitle Processing :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Subtitle File</b> → Upload subtitle file
┠ <b>Subtitle Embed</b> → Embed subtitles in video
┠ <b>Subtitle Burn</b> → Burn subtitles permanently
┠ <b>Subtitle Style</b> → Configure subtitle appearance
┠ <b>Subtitle Position</b> → Set subtitle position
┖ <b>Subtitle Language</b> → Set subtitle language"""

    elif stype == "rename":
        buttons.data_button("Rename Pattern", f"userset {user_id} menu RENAME_PATTERN")
        buttons.data_button("Prefix", f"userset {user_id} menu RENAME_PREFIX")
        buttons.data_button("Suffix", f"userset {user_id} menu RENAME_SUFFIX")
        
        buttons.data_button("Extension Change", f"userset {user_id} menu RENAME_EXTENSION")
        buttons.data_button("Case Change", f"userset {user_id} menu RENAME_CASE_OPTIONS")
        buttons.data_button("Replace Text", f"userset {user_id} menu RENAME_REPLACE_OPTIONS")

        buttons.data_button("Back", f"userset {user_id} video_processing", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        btns = buttons.build_menu(2)

        # Get current rename settings
        rename_pattern = user_dict.get("RENAME_PATTERN", "Not Set")
        rename_prefix = user_dict.get("RENAME_PREFIX", "Not Set")
        rename_suffix = user_dict.get("RENAME_SUFFIX", "Not Set")

        text = f"""⌬ <b>File Rename Configuration :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Rename Pattern</b> → <code>{escape(str(rename_pattern))}</code>
┠ <b>Prefix</b> → <code>{escape(str(rename_prefix))}</code>
┠ <b>Suffix</b> → <code>{escape(str(rename_suffix))}</code>
┠ <b>Extension Change</b> → Modify file extensions
┠ <b>Case Change</b> → Change filename case
┖ <b>Replace Text</b> → Find and replace in filenames"""

    return text, btns


async def update_user_settings(query, stype="main"):
    handler_dict[query.from_user.id] = False
    msg, button = await get_user_settings(query.from_user, stype)
    await edit_message(query.message, msg, button)


@new_task
async def send_user_settings(_, message):
    from_user = message.from_user
    handler_dict[from_user.id] = False
    msg, button = await get_user_settings(from_user)
    await send_message(message, msg, button)


@new_task
async def add_file(_, message, ftype, rfunc):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    if ftype == "THUMBNAIL":
        des_dir = await create_thumb(message, user_id)
    elif ftype == "RCLONE_CONFIG":
        rpath = f"{getcwd()}/rclone/"
        await makedirs(rpath, exist_ok=True)
        des_dir = f"{rpath}{user_id}.conf"
        await message.download(file_name=des_dir)
    elif ftype == "TOKEN_PICKLE":
        tpath = f"{getcwd()}/tokens/"
        await makedirs(tpath, exist_ok=True)
        des_dir = f"{tpath}{user_id}.pickle"
        await message.download(file_name=des_dir)
    elif ftype == "USER_COOKIE_FILE":
        cpath = f"{getcwd()}/cookies/{user_id}"
        await makedirs(cpath, exist_ok=True)
        des_dir = f"{cpath}/cookies.txt"
        await message.download(file_name=des_dir)
    elif ftype == "WATERMARK_IMAGE_PATH":
        wpath = f"{getcwd()}/watermarks/{user_id}"
        await makedirs(wpath, exist_ok=True)
        file_extension = message.document.file_name.split('.')[-1] if message.document and message.document.file_name else "png"
        des_dir = f"{wpath}/watermark.{file_extension}"
        await message.download(file_name=des_dir)
    await delete_message(message)
    update_user_ldata(user_id, ftype, des_dir)
    await rfunc()
    await database.update_user_doc(user_id, ftype, des_dir)


@new_task
async def add_one(_, message, option, rfunc):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    user_dict = user_data.get(user_id, {})
    value = message.text
    if value.startswith("{") and value.endswith("}"):
        try:
            value = eval(value)
            if user_dict[option]:
                user_dict[option].update(value)
            else:
                update_user_ldata(user_id, option, value)
        except Exception as e:
            await send_message(message, str(e))
            return
    else:
        await send_message(message, "It must be Dict!")
        return
    await delete_message(message)
    await rfunc()
    await database.update_user_data(user_id)


@new_task
async def remove_one(_, message, option, rfunc):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    user_dict = user_data.get(user_id, {})
    names = message.text.split("/")
    for name in names:
        if name in user_dict[option]:
            del user_dict[option][name]
    await delete_message(message)
    await rfunc()
    await database.update_user_data(user_id)


@new_task
async def set_option(_, message, option, rfunc):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    if option == "LEECH_SPLIT_SIZE":
        if not value.isdigit():
            value = get_size_bytes(value)
        value = min(int(value), TgClient.MAX_SPLIT_SIZE)
    # elif option == "LEECH_DUMP_CHAT": # TODO: Add
    elif option == "EXCLUDED_EXTENSIONS":
        fx = value.split()
        value = ["aria2", "!qB"]
        for x in fx:
            x = x.lstrip(".")
            value.append(x.strip().lower())
    elif option == "YT_TAGS":
        if isinstance(value, str):
            value = [tag.strip() for tag in value.split(",") if tag.strip()]
        elif not isinstance(value, list):
            await send_message(message, "YT Tags must be a comma-separated string.")
            return
    elif option == "YT_CATEGORY_ID":
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        elif not isinstance(value, int):
            await send_message(message, "YT Category ID must be a whole number.")
            return
    elif option == "YT_PRIVACY_STATUS":
        allowed_statuses = ["public", "private", "unlisted"]
        if not isinstance(value, str) or value.lower() not in allowed_statuses:
            await send_message(
                message,
                f"YT Privacy Status must be one of: {', '.join(allowed_statuses)}.",
            )
            return
        value = value.lower()
    elif option in [
        "METADATA",
        "AUDIO_METADATA",
        "VIDEO_METADATA",
        "SUBTITLE_METADATA",
    ]:
        parsed_metadata_dict = {}
        if value and isinstance(value, str):
            if value.strip() == "":
                value = {}
            else:
                parts = []
                current = ""
                i = 0
                while i < len(value):
                    if value[i] == "\\" and i + 1 < len(value) and value[i + 1] == "|":
                        current += "|"
                        i += 2
                    elif value[i] == "|":
                        parts.append(current)
                        current = ""
                        i += 1
                    else:
                        current += value[i]
                        i += 1
                if current:
                    parts.append(current)

                for part in parts:
                    if "=" in part:
                        key, val_str = part.split("=", 1)
                        parsed_metadata_dict[key.strip()] = val_str.strip()
                if not parsed_metadata_dict and value.strip() != "":
                    await send_message(
                        message,
                        "Malformed metadata string. Format: key1=value1|key2=value2. Use \\| to escape pipe characters.",
                    )
                    return
                value = parsed_metadata_dict
        else:
            value = {}

    elif option in ["UPLOAD_PATHS", "FFMPEG_CMDS", "YT_DLP_OPTIONS"]:
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(sub(r"\s+", " ", value))
            except Exception as e:
                await send_message(message, str(e))
                return
        else:
            await send_message(message, "It must be dict!")
            return
    elif option == "VIDEO_ENCODE_PRESET":
        allowed_presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
        if value not in allowed_presets:
            await send_message(message, f"Invalid preset. Please select from: {', '.join(allowed_presets)}")
            return
    elif option == "VIDEO_ENCODE_QUALITY":
        allowed_qualities = ["1080p", "720p", "576p", "480p", "360p", "Original"]
        if value not in allowed_qualities:
            await send_message(message, f"Invalid quality. Please select from: {', '.join(allowed_qualities)}")
            return
    elif option == "VIDEO_ENCODE_CRF":
        try:
            crf_value = int(value)
            if not (0 <= crf_value <= 51):
                await send_message(message, "CRF must be between 0 and 51.")
                return
            value = crf_value
        except ValueError:
            await send_message(message, "CRF must be a number between 0 and 51.")
            return
    elif option == "VIDEO_ENCODE_AUDIO_BITRATE":
        allowed_bitrates = ["64k", "96k", "128k", "192k", "256k", "320k"]
        if value not in allowed_bitrates:
            await send_message(message, f"Invalid audio bitrate. Please select from: {', '.join(allowed_bitrates)}")
            return
    elif option == "WATERMARK_OPACITY":
        try:
            opacity_value = float(value)
            if not (0.0 <= opacity_value <= 1.0):
                await send_message(message, "Opacity must be between 0.0 and 1.0.")
                return
            value = opacity_value
        except ValueError:
            await send_message(message, "Opacity must be a number between 0.0 and 1.0.")
            return
    elif option == "WATERMARK_COLOR":
        if not value.startswith("#") or len(value) != 7:
            await send_message(message, "Color must be in hex format like '#FFFFFF'.")
            return
    elif option == "WATERMARK_POSITION":
        allowed_positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
        if value not in allowed_positions:
            await send_message(message, f"Invalid position. Please select from: {', '.join(allowed_positions)}")
            return
    elif option == "WATERMARK_TYPE":
        allowed_types = ["text", "image"]
        if value not in allowed_types:
            await send_message(message, f"Invalid watermark type. Please select from: {', '.join(allowed_types)}")
            return
    elif option == "WATERMARK_SIZE":
        allowed_sizes = ["small", "medium", "large"]
        if value not in allowed_sizes:
            await send_message(message, f"Invalid size. Please select from: {', '.join(allowed_sizes)}")
            return
    elif option == "WATERMARK_DURATION":
        allowed_durations = ["full", "start", "end", "custom"]
        if value not in allowed_durations:
            await send_message(message, f"Invalid duration. Please select from: {', '.join(allowed_durations)}")
            return
    elif option == "WATERMARK_TEXT_BG":
        if value.lower() in ["true", "1", "yes"]:
            value = True
        elif value.lower() in ["false", "0", "no"]:
            value = False
        else:
            await send_message(message, "Text background must be true or false.")
            return
    elif option == "KEEP_SOURCE":
        if value.lower() in ["true", "1", "yes"]:
            value = True
        elif value.lower() in ["false", "0", "no"]:
            value = False
        else:
            await send_message(message, "Keep source must be true or false.")
            return
    elif option in ["STREAM_EXTRACT_OPTIONS", "STREAM_REMOVE_OPTIONS", "STREAM_SWAP_OPTIONS"]:
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(sub(r"\s+", " ", value))
            except Exception as e:
                await send_message(message, str(e))
                return
        else:
            await send_message(message, "It must be dict!")
            return
    elif option in ["VIDEO_MERGE_OPTIONS", "VIDEO_OVERLAY_OPTIONS", "VIDEO_CONCAT_OPTIONS", "VIDEO_SPLIT_OPTIONS"]:
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(sub(r"\s+", " ", value))
            except Exception as e:
                await send_message(message, str(e))
                return
        else:
            await send_message(message, "It must be dict!")
            return
    elif option in ["AUDIO_MIX_OPTIONS", "AUDIO_REPLACE_OPTIONS", "AUDIO_SYNC_OPTIONS", "AUDIO_VOLUME_OPTIONS"]:
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(sub(r"\s+", " ", value))
            except Exception as e:
                await send_message(message, str(e))
                return
        else:
            await send_message(message, "It must be dict!")
            return
    elif option in ["SUBTITLE_EMBED_OPTIONS", "SUBTITLE_BURN_OPTIONS", "SUBTITLE_STYLE_OPTIONS", "SUBTITLE_POSITION_OPTIONS", "SUBTITLE_LANGUAGE_OPTIONS"]:
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(sub(r"\s+", " ", value))
            except Exception as e:
                await send_message(message, str(e))
                return
        else:
            await send_message(message, "It must be dict!")
            return
    elif option == "RENAME_CASE_OPTIONS":
        allowed_cases = ["upper", "lower", "title"]
        if value not in allowed_cases:
            await send_message(message, f"Invalid case option. Please select from: {', '.join(allowed_cases)}")
            return
    elif option == "RENAME_REPLACE_OPTIONS":
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(sub(r"\s+", " ", value))
            except Exception as e:
                await send_message(message, str(e))
                return
        else:
            await send_message(message, "It must be dict!")
            return
    update_user_ldata(user_id, option, value)
    await delete_message(message)
    await rfunc()
    await database.update_user_data(user_id)


async def get_menu(option, message, user_id):
    handler_dict[user_id] = False
    user_dict = user_data.get(user_id, {})

    file_dict = {
        "THUMBNAIL": f"thumbnails/{user_id}.jpg",
        "RCLONE_CONFIG": f"rclone/{user_id}.conf",
        "TOKEN_PICKLE": f"tokens/{user_id}.pickle",
        "USER_COOKIE_FILE": f"cookies/{user_id}/cookies.txt",
    }

    buttons = ButtonMaker()
    if option in ["THUMBNAIL", "RCLONE_CONFIG", "TOKEN_PICKLE", "USER_COOKIE_FILE"]:
        key = "file"
    else:
        key = "set"
    buttons.data_button(
        "Change" if user_dict.get(option, False) else "Set",
        f"userset {user_id} {key} {option}",
    )
    if user_dict.get(option, False):
        if option == "THUMBNAIL":
            buttons.data_button(
                "View Thumb", f"userset {user_id} view THUMBNAIL", "header"
            )
        elif option in ["YT_DLP_OPTIONS", "FFMPEG_CMDS", "UPLOAD_PATHS"]:
            buttons.data_button(
                "Add One", f"userset {user_id} addone {option}", "header"
            )
            buttons.data_button(
                "Remove One", f"userset {user_id} rmone {option}", "header"
            )

        if key != "file":  # TODO: option default val check
            buttons.data_button("Reset", f"userset {user_id} reset {option}")
        elif await aiopath.exists(file_dict[option]):
            buttons.data_button("Remove", f"userset {user_id} remove {option}")
    if option in leech_options:
        back_to = "leech"
    elif option in rclone_options:
        back_to = "rclone"
    elif option in gdrive_options:
        back_to = "gdrive"
    elif option in yt_options:
        back_to = "yttools"
    elif option in ffset_options:
        back_to = "ffset"
    elif option in advanced_options:
        back_to = "advanced"
    elif option in video_encode_options:
        back_to = "video_encode"
    elif option in watermark_options:
        back_to = "watermark"
    elif option in stream_options:
        back_to = "ffset"  # Stream options go back to FF settings
    else:
        back_to = "back"
    buttons.data_button("Back", f"userset {user_id} {back_to}", "footer")
    buttons.data_button("Close", f"userset {user_id} close", "footer")
    val = user_dict.get(option)
    if option in file_dict and await aiopath.exists(file_dict[option]):
        val = "<b>Exists</b>"
    elif option == "LEECH_SPLIT_SIZE":
        val = get_readable_file_size(val)
    elif option == "METADATA":
        current_meta_val = user_dict.get(option)
        if isinstance(current_meta_val, dict) and current_meta_val:
            val = ", ".join(
                f"{k}={escape(str(v))}" for k, v in current_meta_val.items()
            )
            val = f"<code>{val}</code>"
        elif isinstance(current_meta_val, str) and current_meta_val:
            val = (
                f"<code>{escape(current_meta_val)}</code> [<i>Legacy, needs re-set</i>]"
            )
        elif not current_meta_val:
            val = "<b>Not Set</b>"

        if val is None:
            val = "<b>Not Exists</b>"

    if option == "METADATA":
        text = f"""⌬ <b><u>Menu Settings :</u></b>
│
┟ <b>Option</b> → {option}
┃
┠ <b>Option's Value</b> → {val if val else "<b>Not Exists</b>"}
┃
┠ <b>Default Input Type</b> → {user_settings_text[option][0]}
┠ <b>Description</b> → {user_settings_text[option][1]}
┃
┠ <b>Dynamic Variables:</b>
┠ • <code>{{filename}}</code> - Full filename
┠ • <code>{{basename}}</code> - Filename without extension  
┠ • <code>{{extension}}</code> - File extension
┃
┠ • <code>{{audiolang}}</code> - Audio language
┖ • <code>{{sublang}}</code> - Subtitle language
"""
    else:
        text = f"""⌬ <b><u>Menu Settings :</u></b>
│
┟ <b>Option</b> → {option}
┃
┠ <b>Option's Value</b> → {val if val else "<b>Not Exists</b>"}
┃
┠ <b>Default Input Type</b> → {user_settings_text[option][0]}
┖ <b>Description</b> → {user_settings_text[option][1]}
"""
    await edit_message(message, text, buttons.build_menu(2))


async def event_handler(client, query, pfunc, rfunc, photo=False, document=False):
    user_id = query.from_user.id
    handler_dict[user_id] = True
    start_time = update_time = time()

    async def event_filter(_, __, event):
        if photo:
            mtype = event.photo or event.document
        elif document:
            mtype = event.document
        else:
            mtype = event.text
        user = event.from_user or event.sender_chat
        return bool(
            user.id == user_id and event.chat.id == query.message.chat.id and mtype
        )

    handler = client.add_handler(
        MessageHandler(pfunc, filters=create(event_filter)), group=-1
    )

    while handler_dict[user_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[user_id] = False
            await rfunc()
        elif time() - update_time > 8 and handler_dict[user_id]:
            update_time = time()
            msg = await client.get_messages(query.message.chat.id, query.message.id)
            text = msg.text.split("\n")
            text[-1] = (
                f"┖ <b>Time Left :</b> <code>{round(60 - (time() - start_time), 2)} sec</code>"
            )
            await edit_message(msg, "\n".join(text), msg.reply_markup)
    client.remove_handler(*handler)


@new_task
async def edit_user_settings(client, query):
    from_user = query.from_user
    user_id = from_user.id
    name = from_user.mention
    message = query.message
    data = query.data.split()

    handler_dict[user_id] = False
    thumb_path = f"thumbnails/{user_id}.jpg"
    rclone_conf = f"rclone/{user_id}.conf"
    token_pickle = f"tokens/{user_id}.pickle"
    yt_cookie_path = f"cookies/{user_id}/cookies.txt"

    user_dict = user_data.get(user_id, {})
    if user_id != int(data[1]):
        return await query.answer("Not Yours!", show_alert=True)
    elif data[2] == "setevent":
        await query.answer()
    elif data[2] in [
        "general",
        "mirror",
        "leech",
        "ffset",
        "advanced",
        "gdrive",
        "rclone",
    ]:
        await query.answer()
        await update_user_settings(query, data[2])
    elif data[2] == "yttools":
        await query.answer()
        await update_user_settings(query, data[2])
    elif data[2] in [
        "video_encode",
        "video_quality",
        "video_crf",
        "audio_bitrate",
        "video_preset",
        "video_processing",
        "watermark",
        "video_video",
        "video_audio",
        "video_subtitle",
        "rename",
    ]:
        await query.answer()
        await update_user_settings(query, data[2])
    elif data[2] == "menu":
        await query.answer()
        await get_menu(data[3], message, user_id)
    elif data[2] == "tog":
        await query.answer()
        update_user_ldata(user_id, data[3], data[4] == "t")
        if data[3] == "STOP_DUPLICATE":
            back_to = "gdrive"
        elif data[3] in ["USER_TOKENS", "USE_DEFAULT_COOKIE"]:
            back_to = "general"
        else:
            back_to = "leech"
        await update_user_settings(query, stype=back_to)
        await database.update_user_data(user_id)
    elif data[2] == "file":
        await query.answer()
        buttons = ButtonMaker()
        text = user_settings_text[data[3]][2]
        buttons.data_button("Stop", f"userset {user_id} menu {data[3]} stop")
        buttons.data_button("Back", f"userset {user_id} menu {data[3]}", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        prompt_title = data[3].replace("_", " ").title()
        new_message_text = f"⌬ <b>Set {prompt_title}</b>\n\n{text}"
        await edit_message(message, new_message_text, buttons.build_menu(1))
        rfunc = partial(get_menu, data[3], message, user_id)
        pfunc = partial(add_file, ftype=data[3], rfunc=rfunc)
        await event_handler(
            client,
            query,
            pfunc,
            rfunc,
            photo=data[3] == "THUMBNAIL",
            document=data[3] != "THUMBNAIL",
        )
    elif data[2] in ["set", "addone", "rmone"]:
        await query.answer()
        buttons = ButtonMaker()
        if data[2] == "set":
            text = user_settings_text[data[3]][2]
            func = set_option
        elif data[2] == "addone":
            text = f"Add one or more string key and value to {data[3]}. Example: {{'key 1': 62625261, 'key 2': 'value 2'}}. Timeout: 60 sec"
            func = add_one
        elif data[2] == "rmone":
            text = f"Remove one or more key from {data[3]}. Example: key 1/key2/key 3. Timeout: 60 sec"
            func = remove_one
        buttons.data_button("Stop", f"userset {user_id} menu {data[3]} stop")
        buttons.data_button("Back", f"userset {user_id} menu {data[3]}", "footer")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        await edit_message(
            message, message.text.html + "\n\n" + text, buttons.build_menu(1)
        )
        rfunc = partial(get_menu, data[3], message, user_id)
        pfunc = partial(func, option=data[3], rfunc=rfunc)
        await event_handler(client, query, pfunc, rfunc)
    elif data[2] == "set_quality":
        await query.answer()
        update_user_ldata(user_id, "VIDEO_ENCODE_QUALITY", data[3])
        await update_user_settings(query, stype="video_quality")
        await database.update_user_data(user_id)
    elif data[2] == "set_crf":
        await query.answer()
        update_user_ldata(user_id, "VIDEO_ENCODE_CRF", int(data[3]))
        await update_user_settings(query, stype="video_crf")
        await database.update_user_data(user_id)
    elif data[2] == "set_audio_bitrate":
        await query.answer()
        update_user_ldata(user_id, "VIDEO_ENCODE_AUDIO_BITRATE", data[3])
        await update_user_settings(query, stype="audio_bitrate")
        await database.update_user_data(user_id)
    elif data[2] == "set_preset":
        await query.answer()
        update_user_ldata(user_id, "VIDEO_ENCODE_PRESET", data[3])
        await update_user_settings(query, stype="video_preset")
        await database.update_user_data(user_id)
    elif data[2] == "remove":
        await query.answer("Removed!", show_alert=True)
        if data[3] in [
            "THUMBNAIL",
            "RCLONE_CONFIG",
            "TOKEN_PICKLE",
            "USER_COOKIE_FILE",
        ]:
            if data[3] == "THUMBNAIL":
                fpath = thumb_path
            elif data[3] == "RCLONE_CONFIG":
                fpath = rclone_conf
            elif data[3] == "USER_COOKIE_FILE":
                fpath = yt_cookie_path
            else:
                fpath = token_pickle
            if await aiopath.exists(fpath):
                await remove(fpath)
            del user_dict[data[3]]
            await database.update_user_doc(user_id, data[3])
        else:
            update_user_ldata(user_id, data[3], "")
            await database.update_user_data(user_id)
        await get_menu(data[3], message, user_id)
    elif data[2] == "reset":
        await query.answer("Reset Done!", show_alert=True)
        user_dict.pop(data[3], None)
        await database.update_user_data(user_id)
        await get_menu(data[3], message, user_id)
    elif data[2] == "confirm_reset_all":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("Yes", f"userset {user_id} do_reset_all yes")
        buttons.data_button("No", f"userset {user_id} do_reset_all no")
        buttons.data_button("Close", f"userset {user_id} close", "footer")
        text = "<i>Are you sure you want to reset all your user settings?</i>"
        await edit_message(query.message, text, buttons.build_menu(2))
    elif data[2] == "do_reset_all":
        if data[3] == "yes":
            await query.answer("Reset Done!", show_alert=True)
            user_dict = user_data.get(user_id, {})
            for k in list(user_dict.keys()):
                if k not in ("SUDO", "AUTH", "VERIFY_TOKEN", "VERIFY_TIME"):
                    del user_dict[k]
            for fpath in [thumb_path, rclone_conf, token_pickle, yt_cookie_path]:
                if await aiopath.exists(fpath):
                    await remove(fpath)
            await update_user_settings(query)
            await database.update_user_data(user_id)
        else:
            await query.answer("Reset Cancelled.", show_alert=True)
            await update_user_settings(query)
    elif data[2] == "view":
        await query.answer()
        await send_file(message, thumb_path, name)
    elif data[2] in ["gd", "rc"]:
        await query.answer()
        du = "rc" if data[2] == "gd" else "gd"
        update_user_ldata(user_id, "DEFAULT_UPLOAD", du)
        await update_user_settings(query, stype="general")
        await database.update_user_data(user_id)
    elif data[2] == "back":
        await query.answer()
        stype = data[3] if len(data) == 4 else "main"
        await update_user_settings(query, stype)
    else:
        await query.answer()
        await delete_message(message, message.reply_to_message)


@new_task
async def get_users_settings(_, message):
    msg = ""
    if auth_chats:
        msg += f"AUTHORIZED_CHATS: {auth_chats}\n"
    if sudo_users:
        msg += f"SUDO_USERS: {sudo_users}\n\n"
    if user_data:
        for u, d in user_data.items():
            kmsg = f"\n<b>{u}:</b>\n"
            if vmsg := "".join(
                f"{k}: <code>{v or None}</code>\n" for k, v in d.items()
            ):
                msg += kmsg + vmsg
        if not msg:
            await send_message(message, "No users data!")
            return
        msg_ecd = msg.encode()
        if len(msg_ecd) > 4000:
            with BytesIO(msg_ecd) as ofile:
                ofile.name = "users_settings.txt"
                await send_file(message, ofile)
        else:
            await send_message(message, msg)
    else:
        await send_message(message, "No users data!")
