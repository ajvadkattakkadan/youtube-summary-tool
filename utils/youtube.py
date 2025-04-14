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
        yt = YouTube(url)
        video_id = extract_video_id(url)
        
        # Check if length exists and handle possible None values
        duration_sec = yt.length if hasattr(yt, 'length') and yt.length is not None else 0
        
        # Format duration
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        duration = f"{minutes}:{seconds:02d}"
        
        # Check other attributes
        title = yt.title if hasattr(yt, 'title') and yt.title is not None else "Unknown Title"
        author = yt.author if hasattr(yt, 'author') and yt.author is not None else "Unknown Channel"
        thumbnail_url = yt.thumbnail_url if hasattr(yt, 'thumbnail_url') and yt.thumbnail_url is not None else ""
        
        return {
            'title': title,
            'channel': author,
            'thumbnail_url': thumbnail_url,
            'video_id': video_id,
            'url': url,
            'duration': duration
        }
    except Exception as e:
        # Log the specific error for debugging
        logging.error(f"Error in get_video_info: {str(e)}")
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