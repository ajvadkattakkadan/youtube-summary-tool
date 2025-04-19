import re
import logging
import traceback

from pytubefix import YouTube

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

logging.basicConfig(level=logging.INFO)

def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL using a simple regex."""
    match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def safe_get_attr(obj, attr_name, default_value):
    """
    Safely gets an attribute from obj. 
    If there's an exception or it's None, return default_value.
    """
    try:
        val = getattr(obj, attr_name, None)
        if val is None:
            return default_value
        return val
    except Exception as e:
        logging.warning(f"Failed to retrieve attribute '{attr_name}': {str(e)}")
        return default_value

def get_video_info(url: str) -> dict:
    """
    Get information (title, channel, thumbnail, video_id, url, and duration) for a YouTube video,
    with extra checks to prevent NoneType or internal pytubefix errors.
    """
    try:
        logging.info(f"--- get_video_info START | URL: {url} ---")
        
        # Extract video_id first, as we'll need it for all methods
        video_id = extract_video_id(url)
        logging.info(f"Extracted video ID: {video_id}")
        
        # First try using pytubefix
        try:
            yt = YouTube(url)
            
            # Attempt to call watch_html to force loading of video info
            logging.info("Attempting to call yt.watch_html")
            _ = yt.watch_html
            
            # Add delay to avoid rate limiting
            import time
            time.sleep(1)
            
            # Log all attributes to debug
            logging.info(f"Video title from PyTube: {getattr(yt, 'title', 'Not found')}")
            logging.info(f"Channel name from PyTube: {getattr(yt, 'author', 'Not found')}")
            
            # 1) We attempt to retrieve the "title," "author," "thumbnail_url" attributes defensively.
            video_title = safe_get_attr(yt, 'title', None)
            channel_name = safe_get_attr(yt, 'author', None)
            thumbnail_url = safe_get_attr(yt, 'thumbnail_url', '')

            # 2) Attempt to fetch videoDetails.lengthSeconds from player_response
            raw_length_seconds = None
            if hasattr(yt, 'player_response'):
                player_resp = yt.player_response or {}
                video_details = player_resp.get('videoDetails', {})
                raw_length_seconds = video_details.get('lengthSeconds', None)
                logging.info(f"lengthSeconds from player_response: {raw_length_seconds}")

            # 3) Convert lengthSeconds to int, if possible
            duration_sec = 0
            if raw_length_seconds is not None:
                try:
                    duration_sec = int(raw_length_seconds)
                except (TypeError, ValueError):
                    logging.warning("Failed to convert player_response lengthSeconds to int.")

            # 4) If still 0, try yt.length
            if duration_sec == 0:
                length_attr = safe_get_attr(yt, 'length', 0)
                if isinstance(length_attr, (int, float)):
                    duration_sec = length_attr
                else:
                    try:
                        duration_sec = int(length_attr)  # final fallback
                    except (TypeError, ValueError):
                        duration_sec = 0

            # 5) Build mm:ss
            minutes, seconds = divmod(int(duration_sec), 60)
            duration_str = f"{minutes}:{seconds:02d}"
            
            # If we got a valid title and channel, use them
            if video_title and channel_name:
                logging.info(f"Successfully retrieved video info via PyTube: {video_title}")
                
                return {
                    'title': video_title,
                    'channel': channel_name,
                    'thumbnail_url': thumbnail_url or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    'video_id': video_id if video_id else "",
                    'url': url,
                    'duration': duration_str
                }
        
        except Exception as e:
            logging.warning(f"PyTube approach failed: {str(e)}")
        
        # If PyTube approach failed, try a simple fallback to get at least some information
        logging.info("Falling back to basic video information")
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        # Use video_id as part of the title to make it somewhat identifiable
        return {
            'title': f"YouTube Video ({video_id})",
            'channel': "YouTube Channel",
            'thumbnail_url': thumbnail_url,
            'video_id': video_id if video_id else "",
            'url': url,
            'duration': "0:00"
        }
        
    except Exception as e:
        logging.error(f"Exception in get_video_info: {str(e)}")
        logging.error(traceback.format_exc())
        raise Exception(f"Failed to get video info: {str(e)}")

def get_transcript(url):
    """Get the transcript for a YouTube video with retry logic."""
    import time
    import random
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            video_id = extract_video_id(url)
            if not video_id:
                raise Exception("Invalid YouTube URL")
            
            # Get the transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine all transcript pieces into one text
            transcript_text = ' '.join([item['text'] for item in transcript_list])
            
            return transcript_text
        
        except Exception as e:
            error_message = str(e)
            
            # Check if it's a rate limiting error
            if "429" in error_message and "Too Many Requests" in error_message:
                if attempt < max_retries - 1:
                    # Add jitter to avoid synchronized retries
                    sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(sleep_time)
                    continue
                else:
                    raise Exception("YouTube is rate limiting requests. Please try again later.")
            
            # Check if it's a missing transcript error
            elif "Could not retrieve a transcript" in error_message:
                raise Exception("This video doesn't have subtitles or closed captions available. Please try a different video.")
            
            # Other errors
            else:
                raise Exception(f"Failed to get transcript: {error_message}")