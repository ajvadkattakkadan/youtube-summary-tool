import re
import logging
import traceback

from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

logging.basicConfig(level=logging.INFO)


def extract_video_id(url):
    """
    Extract the video ID from a YouTube URL.

    We look for a pattern of exactly 11 characters (letters, digits, underscores, or hyphens)
    following 'v=' or a slash. Example:
    https://www.youtube.com/watch?v=VIDEO_ID
    https://youtu.be/VIDEO_ID
    """
    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    return None


def get_video_info(url):
    """
    Get information about a YouTube video (title, channel, thumbnail, video_id, url, duration).
    Fallback to '0:00' if video length is missing or invalid.
    """
    try:
        logging.info(f"Starting get_video_info with URL: {url}")
        yt = YouTube(url)

        video_id = extract_video_id(url)
        logging.info(f"Extracted video ID: {video_id}")

        # Attempt to retrieve video length from PyTube's player_response
        # as a more reliable fallback than yt.length
        raw_length_seconds = None
        if hasattr(yt, 'player_response') and yt.player_response:
            video_details = yt.player_response.get('videoDetails', {})
            raw_length_seconds = video_details.get('lengthSeconds', None)

        # 1) Attempt to convert raw_length_seconds
        duration_sec = None
        if raw_length_seconds is not None:
            try:
                duration_sec = int(raw_length_seconds)
                logging.info(f"Duration found in player_response: {duration_sec} seconds")
            except (TypeError, ValueError):
                logging.warning("Failed to convert lengthSeconds to int in player_response.")

        # 2) If still None, fallback to the original yt.length approach
        if duration_sec is None:
            if hasattr(yt, 'length') and yt.length is not None:
                try:
                    logging.info(f"Converting yt.length to int: {yt.length}")
                    duration_sec = int(yt.length)
                except (TypeError, ValueError):
                    logging.warning("Failed to convert yt.length to int. Defaulting to 0 seconds.")
                    duration_sec = 0
            else:
                logging.info("No valid length found. Defaulting to 0 seconds.")
                duration_sec = 0

        # Convert final duration in mm:ss format
        minutes, seconds = divmod(duration_sec, 60)
        duration = f"{minutes}:{seconds:02d}"

        # Prepare a result dict with safe values
        result = {
            'title': yt.title if hasattr(yt, 'title') and yt.title else "Unknown Title",
            'channel': yt.author if hasattr(yt, 'author') and yt.author else "Unknown Channel",
            'thumbnail_url': yt.thumbnail_url if hasattr(yt, 'thumbnail_url') and yt.thumbnail_url else "",
            'video_id': video_id if video_id else "",
            'url': url,
            'duration': duration
        }

        logging.info(f"Returning video info: {result}")
        return result

    except Exception as e:
        logging.error(f"Exception in get_video_info: {str(e)}")
        logging.error(traceback.format_exc())
        raise Exception(f"Failed to get video info: {str(e)}")


def get_transcript(url):
    """
    Get the transcript for a YouTube video by extracting the video ID
    and using YouTubeTranscriptApi.
    """
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise Exception("Invalid YouTube URL")

        # Retrieve transcript list
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

        # Combine all transcript pieces into a single text block
        transcript_text = ' '.join(item['text'] for item in transcript_list)
        return transcript_text

    except Exception as e:
        logging.error(f"Failed to get transcript for {url}: {str(e)}")
        raise Exception(f"Failed to get transcript: {str(e)}")
