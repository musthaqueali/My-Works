"""
Media Converter Module for 'I LOVE FILES'
Comprehensive Audio and Video Conversion Engine powered by FFmpeg v7.1.
Supports 15+ Audio codecs, 17+ Video formats, Video-to-Audio extraction,
GIF-to-Video, Video-to-GIF, and resolution / bitrate customizations.
"""
import os
import subprocess
import logging
import imageio_ffmpeg

logger = logging.getLogger(__name__)

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

AUDIO_FORMATS = {
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "opus", "wma", 
    "aiff", "ac3", "amr", "m4r", "mp2", "caf", "au"
}

VIDEO_FORMATS = {
    "mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", 
    "3gp", "3g2", "ts", "mts", "m2ts", "mpg", "mpeg", "vob", "ogv", "gif"
}

def is_audio(fmt: str) -> bool:
    return fmt.lower().lstrip(".") in AUDIO_FORMATS

def is_video(fmt: str) -> bool:
    return fmt.lower().lstrip(".") in VIDEO_FORMATS

def convert_media(
    input_path: str, 
    output_path: str, 
    target_format: str, 
    resolution: str = None, 
    bitrate: str = None
) -> bool:
    """
    Universal media converter for Audio and Video formats.
    Handles Audio-to-Audio, Video-to-Video, Video-to-Audio, Video-to-GIF, and GIF-to-Video.
    """
    target_format = target_format.lower().lstrip(".")
    in_ext = os.path.splitext(input_path)[1].lower().lstrip(".")

    cmd = [FFMPEG_BIN, "-y", "-i", input_path]

    # Case 1: Target is GIF (from Video or Animation)
    if target_format == "gif":
        vf = r"fps=15,scale=trunc(min(iw\,480)/2)*2:-2:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        cmd.extend(["-vf", vf, output_path])
        return _run_ffmpeg(cmd)

    # Case 2: Target is Audio (Audio-to-Audio OR Video-to-Audio extraction)
    if is_audio(target_format):
        if is_video(in_ext):
            cmd.append("-vn")

        if target_format == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate or "320k"])
        elif target_format == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif target_format == "flac":
            cmd.extend(["-c:a", "flac"])
        elif target_format == "aac":
            cmd.extend(["-c:a", "aac", "-b:a", bitrate or "192k"])
        elif target_format == "ogg":
            cmd.extend(["-c:a", "libvorbis", "-q:a", "4"])
        elif target_format == "m4a":
            cmd.extend(["-c:a", "aac", "-b:a", bitrate or "192k"])
        elif target_format == "opus":
            cmd.extend(["-c:a", "libopus", "-b:a", bitrate or "128k"])
        elif target_format == "wma":
            cmd.extend(["-c:a", "wmav2", "-b:a", bitrate or "192k"])
        elif target_format == "aiff":
            cmd.extend(["-c:a", "pcm_s16be"])
        elif target_format == "ac3":
            cmd.extend(["-c:a", "ac3", "-b:a", bitrate or "384k"])
        elif target_format == "amr":
            cmd.extend(["-c:a", "libopencore_amrnb", "-ar", "8000", "-ac", "1"])
        elif target_format == "m4r":
            cmd.extend(["-c:a", "aac", "-b:a", bitrate or "192k", "-f", "ipod"])
        elif target_format == "mp2":
            cmd.extend(["-c:a", "mp2", "-b:a", bitrate or "192k"])
        elif target_format == "caf":
            cmd.extend(["-c:a", "pcm_s16be"])
        elif target_format == "au":
            cmd.extend(["-c:a", "pcm_s16be"])
        else:
            cmd.extend(["-b:a", bitrate or "192k"])

        cmd.append(output_path)
        return _run_ffmpeg(cmd)

    # Case 3: Target is Video
    if is_video(target_format):
        vf_filters = []
        if in_ext == "gif":
            vf_filters.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")

        if resolution:
            res_map = {
                "480p": "scale=854:480",
                "720p": "scale=1280:720",
                "1080p": "scale=1920:1080",
                "4k": "scale=3840:2160"
            }
            scale_filter = res_map.get(resolution.lower(), f"scale={resolution}")
            vf_filters.append(scale_filter)

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        if target_format == "mp4":
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart"])
        elif target_format == "mkv":
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])
        elif target_format == "avi":
            cmd.extend(["-c:v", "libxvid", "-c:a", "mp3"])
        elif target_format == "mov":
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])
        elif target_format == "webm":
            cmd.extend(["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-c:a", "libopus"])
        elif target_format == "flv":
            cmd.extend(["-c:v", "flv", "-c:a", "mp3"])
        elif target_format == "wmv":
            cmd.extend(["-c:v", "wmv2", "-c:a", "wmav2"])
        elif target_format == "m4v":
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])
        elif target_format in ("3gp", "3g2"):
            cmd.extend(["-c:v", "h263", "-s", "352x288", "-r", "15", "-c:a", "libopencore_amrnb", "-ar", "8000", "-ac", "1"])
        elif target_format in ("ts", "mts", "m2ts"):
            cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-f", "mpegts"])
        elif target_format in ("mpg", "mpeg", "vob"):
            cmd.extend(["-c:v", "mpeg2video", "-c:a", "mp2"])
        elif target_format == "ogv":
            cmd.extend(["-c:v", "libtheora", "-c:a", "libvorbis"])
        else:
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])

        if bitrate:
            cmd.extend(["-b:v", bitrate])

        cmd.append(output_path)
        return _run_ffmpeg(cmd)

    raise ValueError(f"Unsupported media conversion target: {target_format}")

def _run_ffmpeg(cmd: list) -> bool:
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:] if result.stderr else 'Unknown error'}")
    return True
