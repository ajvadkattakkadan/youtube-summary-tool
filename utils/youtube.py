from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import re
import logging

def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def get_video_info(url):
    """Get information about a YouTube video."""
    try:
        print(f"Starting get_video_info with URL: {url}")
        yt = YouTube(url)
        video_id = extract_video_id(url)
        print(f"Video ID: {video_id}")
        
        # Debug yt object attributes
        print(f"yt.length type: {type(yt.length) if hasattr(yt, 'length') else 'No length attribute'}")
        print(f"yt.length value: {yt.length if hasattr(yt, 'length') else 'No length attribute'}")
        
        # Super defensive approach - don't even try to use yt.length if it's None
        if not hasattr(yt, 'length') or yt.length is None:
            print("Length is None or missing, using default duration")
            duration = "0:00"
        else:
            try:
                print(f"Converting length to int: {yt.length}")
                duration_sec = int(yt.length)
                minutes = duration_sec // 60
                seconds = duration_sec % 60
                duration = f"{minutes}:{seconds:02d}"
                print(f"Calculated duration: {duration}")
            except (TypeError, ValueError) as e:
                print(f"Error converting length: {e}")
                duration = "0:00"
        
        # Prepare return dict with safe values
        result = {
            'title': yt.title if hasattr(yt, 'title') and yt.title is not None else "Unknown Title",
            'channel': yt.author if hasattr(yt, 'author') and yt.author is not None else "Unknown Channel",
            'thumbnail_url': yt.thumbnail_url if hasattr(yt, 'thumbnail_url') and yt.thumbnail_url is not None else "",
            'video_id': video_id if video_id is not None else "",
            'url': url,
            'duration': duration
        }
        print(f"Returning video info: {result}")
        return result
    except Exception as e:
        import traceback
        print(f"Exception in get_video_info: {str(e)}")
        print(traceback.format_exc())
        raise Exception(f"Failed to get video info: {str(e)}")

def get_transcript(url):
    """Get the transcript for a YouTube video."""
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
        raise Exception(f"Failed to get transcript: {str(e)}")