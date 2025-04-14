from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import logging
import re

logging.basicConfig(level=logging.INFO)

def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL using a simple regex."""
    match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def get_transcript(url: str) -> str:
    """
    Get the transcript for a YouTube video in one of the preferred languages.
    If no valid transcript is found, returns an empty string or raises an exception.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL or missing video ID.")

    try:
        # 1. Retrieve the available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 2. Decide which languages you want to try, in order of preference
        preferred_langs = ['en', 'en-IN', 'en-GB', 'en-AU']  # etc.

        # 3. Attempt to fetch a transcript in any of the preferred languages
        for lang in preferred_langs:
            try:
                logging.info(f"Trying language '{lang}' for video {video_id}...")
                transcript = transcript_list.find_transcript([lang])
                # If found, fetch it
                fetched = transcript.fetch()
                
                # 4. Combine into one string
                transcript_text = ' '.join([item['text'] for item in fetched])
                return transcript_text
            except NoTranscriptFound:
                logging.warning(f"No transcript found for language '{lang}'. Trying next...")

        # 5. Optionally, try the "generated" transcript if no manual transcript is available
        # Because auto-generated transcripts might have a language code like 'en' but be flagged as "generated"
        try:
            logging.info("Trying 'generated' transcript for fallback...")
            auto_generated = transcript_list.find_generated_transcript(preferred_langs)
            fetched_auto = auto_generated.fetch()
            transcript_text = ' '.join([item['text'] for item in fetched_auto])
            return transcript_text
        except NoTranscriptFound:
            logging.warning("No generated transcripts found for preferred languages either.")

        # If we exit the loop without returning, no transcripts are available in desired languages
        logging.error(f"No transcripts found for video {video_id} in preferred languages.")
        return ""  # or raise an exception if you prefer

    except TranscriptsDisabled:
        logging.error(f"Transcripts are disabled for this video ({video_id}).")
        return ""  # or raise an exception

    except Exception as e:
        logging.error(f"Failed to get transcript for {url}: {str(e)}")
        raise Exception(f"Failed to get transcript: {str(e)}")


