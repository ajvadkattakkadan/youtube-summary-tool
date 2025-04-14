from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables - useful for local development
load_dotenv()

# Proper approach to get API key with error handling
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Initialize the client with the API key
client = OpenAI(api_key=api_key)

def generate_summary(transcript_text, video_title, max_tokens=500):
    """
    Generate a summary of the YouTube video transcript using OpenAI's API.
    
    Args:
        transcript_text (str): The full transcript text
        video_title (str): The title of the video
        max_tokens (int): Maximum length of the summary
        
    Returns:
        str: The generated summary
    """
    try:
        # Truncate the transcript if it's too long (to avoid token limits)
        max_transcript_length = 4000  # Adjust as needed
        truncated_transcript = transcript_text[:max_transcript_length]
        
        prompt = f"""
        Create a comprehensive summary of the following YouTube video transcript.
        
        Video Title: {video_title}
        
        Transcript:
        {truncated_transcript}
        
        Instructions:
        1. Include the main points and key insights
        2. Structure the summary with clear sections
        3. Maintain a neutral, informative tone
        4. Highlight any important conclusions or takeaways
        """
        
        # Using the correct API endpoint for the OpenAI client
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a more widely available model (change to gpt-4o if you have access)
            messages=[
                {"role": "system", "content": "You are a professional summarizer that creates concise, well-structured summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        
        # Extract the summary from the response
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        import logging
        logging.error(f"Error generating summary: {str(e)}")
        # Return a basic summary or error message when API call fails
        return f"Could not generate summary: {str(e)}"