import re
import logging
import traceback

from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

logging.basicConfig(level=logging.INFO)


def extract_video_id(url: str) -> str:
    """
    Extract the video ID from a YouTube URL using a regex that targets 11-character IDs.
    Returns None if not found.
    """
    match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None


def get_video_info(url: str) -> dict:
    """
    Get information (title, channel, thumbnail, video_id, url, and duration) for a YouTube video,
    with extra checks to prevent NoneType errors during length extraction.
    """
    try:
        logging.info(f"--- get_video_info START | URL: {url} ---")
        yt = YouTube(url)

        video_id = extract_video_id(url)
        logging.info(f"Extracted video ID: {video_id}")

        # 1) Debug basic yt attributes
        logging.info(f"yt.title: {getattr(yt, 'title', None)}")
        logging.info(f"yt.author: {getattr(yt, 'author', None)}")
        logging.info(f"yt.thumbnail_url: {getattr(yt, 'thumbnail_url', None)}")
        logging.info(f"yt.length: {getattr(yt, 'length', None)}")

        # 2) Debug player_response
        if hasattr(yt, 'player_response'):
            logging.info("Checking yt.player_response for videoDetails...")
            player_resp = yt.player_response
            # Print top-level keys for debugging
            logging.info(f"player_response keys: {list(player_resp.keys())}")
            video_details = player_resp.get('videoDetails', {})
            logging.info(f"videoDetails keys: {list(video_details.keys())}")
            raw_length_seconds = video_details.get('lengthSeconds', None)
            logging.info(f"lengthSeconds from videoDetails: {raw_length_seconds}")
        else:
            logging.info("No player_response found in yt object.")
            raw_length_seconds = None

        # 3) Attempt to parse raw_length_seconds
        #    If it's still None or fails conversion, set to 0
        duration_sec = 0
        if raw_length_seconds is not None:
            try:
                duration_sec = int(raw_length_seconds)
                logging.info(f"Parsed lengthSeconds into duration_sec={duration_sec}")
            except (TypeError, ValueError):
                logging.warning("Failed to convert lengthSeconds to int. Falling back to 0.")

        # 4) Fallback to yt.length if duration_sec is still 0
        if duration_sec == 0 and hasattr(yt, 'length') and yt.length is not None:
            try:
                logging.info(f"Attempting fallback with yt.length: {yt.length}")
                duration_sec = int(yt.length)
                logging.info(f"Converted yt.length to duration_sec={duration_sec}")
            except (TypeError, ValueError):
                logging.warning("Failed to convert yt.length to int. Using 0 as final fallback.")

        # 5) Convert final duration in mm:ss format
        minutes, seconds = divmod(duration_sec, 60)
        duration_str = f"{minutes}:{seconds:02d}"

        # 6) Compile results
        result = {
            'title': yt.title if getattr(yt, 'title', None) else "Unknown Title",
            'channel': yt.author if getattr(yt, 'author', None) else "Unknown Channel",
            'thumbnail_url': yt.thumbnail_url if getattr(yt, 'thumbnail_url', None) else "",
            'video_id': video_id if video_id else "",
            'url': url,
            'duration': duration_str
        }

        logging.info(f"Final video info: {result}")
        logging.info("--- get_video_info END ---\n")
        return result

    except Exception as e:
        logging.error(f"Exception in get_video_info: {str(e)}")
        logging.error(traceback.format_exc())
        raise Exception(f"Failed to get video info: {str(e)}")


def get_transcript(url: str) -> str:
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


if __name__ == "__main__":
    # For testing purposes
    test_url = "https://www.youtube.com/watch?v=EXAMPLE_ID"
    try:
        info = get_video_info(test_url)
        print("Video Info:", info)
    except Exception as err:
        print("An error occurred:", err)
