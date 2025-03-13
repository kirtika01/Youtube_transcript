from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re
from dotenv import load_dotenv

load_dotenv()

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    # YouTube URL patterns
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\?\/]+)',
        r'youtube.com/watch\?.*v=([^&]+)',
        r'youtube.com/shorts/([^&\?\/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def get_video_info(url):
    """Get video title and other metadata using yt-dlp."""
    try:
        video_id = extract_video_id(url)
        # First try to get just the metadata without downloading
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'format': 'best',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'author': info.get('uploader', 'Unknown Author'),
                    'length': info.get('duration', 0),
                    'thumbnail_url': info.get('thumbnail', '')
                }
            except Exception as e:
                # If yt-dlp fails, try using just the video ID for basic info
                return {
                    'title': f'Video {video_id}',
                    'author': 'Unknown Author',
                    'length': 0,
                    'thumbnail_url': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
                }
    except Exception as e:
        raise ValueError(f"Error fetching video info: {str(e)}")

def get_youtube_transcript(video_id):
    """Get transcript from YouTube video if available."""
    try:
        # Get list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # Try to get English transcript first
            transcript = transcript_list.find_transcript(['en'])
        except:
            # If English not available, get auto-generated transcript
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                # If no English, get the first available transcript
                try:
                    transcript = transcript_list.find_manually_created_transcript()
                except:
                    return None

        # Fetch the transcript
        transcript_data = transcript.fetch()
        return ' '.join([entry['text'] for entry in transcript_data])
    except Exception:
        return None  # Return None if transcript is not available