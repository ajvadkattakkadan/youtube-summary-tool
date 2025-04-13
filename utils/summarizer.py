from openai import OpenAI
import os

# Set your OpenAI API key
# openai.api_key = os.environ.get("OPENAI_API_KEY")  # Uncomment and set via environment variable
OpenAI.api_key = os.environ["OPENAI_API_KEY"]  # Replace with your actual API key
client = OpenAI()
if not OpenAI.api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
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
    
    response = client.responses.create(
        model="gpt-4o",
        instructions="Summarice.",  # Choose appropriate model
        input=prompt
        
        
    )
    
    summary = response.output_text
    return summary