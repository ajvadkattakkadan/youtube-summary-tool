from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import re

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
        
        # Format duration
        duration_sec = yt.length
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        duration = f"{minutes}:{seconds:02d}"
        
        return {
            'title': yt.title,
            'channel': yt.author,
            'thumbnail_url': yt.thumbnail_url,
            'video_id': video_id,
            'url': url,
            'duration': duration
        }
    except Exception as e:
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