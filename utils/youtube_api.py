from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import logging

# Get API key from environment variable
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

def extract_video_id(url):
    """Extract YouTube video ID from URL."""
    import re
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def get_video_info(url):
    """Get video information using the YouTube Data API."""
    try:
        logging.info(f"--- get_video_info START | URL: {url} ---")
        
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
            
        logging.info(f"Extracted video ID: {video_id}")
        
        # Check if API key is available
        if not YOUTUBE_API_KEY:
            logging.error("YouTube API key not found in environment variables")
            raise ValueError("YouTube API key not configured")
            
        # Initialize the YouTube API client
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # Get video details
        video_response = youtube.videos().list(
            part='snippet,contentDetails',
            id=video_id
        ).execute()
        
        # Check if video exists
        if not video_response.get('items'):
            logging.warning(f"No video found for ID: {video_id}")
            raise ValueError(f"Video not found: {video_id}")
            
        # Extract video information
        video_data = video_response['items'][0]
        snippet = video_data['snippet']
        content_details = video_data['contentDetails']
        
        # Process duration (in ISO 8601 format, e.g. PT1H2M3S)
        duration_iso = content_details.get('duration', 'PT0M0S')
        
        # Convert ISO 8601 duration to minutes:seconds
        import re
        import datetime
        
        # Extract hours, minutes, seconds
        hours = re.search(r'(\d+)H', duration_iso)
        minutes = re.search(r'(\d+)M', duration_iso)
        seconds = re.search(r'(\d+)S', duration_iso)
        
        hours = int(hours.group(1)) if hours else 0
        minutes = int(minutes.group(1)) if minutes else 0
        seconds = int(seconds.group(1)) if seconds else 0
        
        # Calculate total duration in seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        # Format as MM:SS or H:MM:SS
        if hours > 0:
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes}:{seconds:02d}"
            
        # Get the best thumbnail available
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_url = thumbnails.get('maxres', {}).get('url') or \
                        thumbnails.get('high', {}).get('url') or \
                        thumbnails.get('medium', {}).get('url') or \
                        thumbnails.get('default', {}).get('url') or \
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                        
        # Create result dictionary
        result = {
            'title': snippet.get('title', f"Video {video_id}"),
            'channel': snippet.get('channelTitle', 'YouTube Channel'),
            'thumbnail_url': thumbnail_url,
            'video_id': video_id,
            'url': url,
            'duration': duration_str
        }
        
        logging.info(f"Final video info from API: {result}")
        return result
        
    except HttpError as e:
        logging.error(f"YouTube API error: {e.resp.status} {e.content}")
        if e.resp.status == 403:
            logging.error("API quota exceeded or API key invalid")
        raise Exception(f"YouTube API error: {str(e)}")
        
    except Exception as e:
        logging.error(f"Error in get_video_info: {str(e)}")
        raise Exception(f"Failed to get video info: {str(e)}")