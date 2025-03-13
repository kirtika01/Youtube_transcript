import whisper
import tempfile
import yt_dlp
import os
import random
import time

class TranscriptionService:
    def __init__(self):
        self.model = None

    def load_model(self, model_size="base"):
        """Load the Whisper model."""
        if self.model is None:
            self.model = whisper.load_model(model_size, device="cpu", in_memory=True)
        return self.model

    def _download_with_retry(self, url, ydl_opts, max_retries=3, initial_delay=1):
        """Attempt download with exponential backoff retry."""
        last_exception = None
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return True
            except Exception as e:
                last_exception = e
                if "HTTP Error 403" in str(e):
                    # Add jitter to delay
                    jitter = random.uniform(0, 0.1) * delay
                    time.sleep(delay + jitter)
                    delay *= 2  # Exponential backoff
                    continue
                else:
                    raise e  # Re-raise if it's not a 403 error

        if last_exception:
            raise last_exception

    def download_audio(self, url):
        """Download audio from YouTube video using yt-dlp."""
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            time.sleep(random.uniform(0.1, 0.5))  # Add small random delay before request
            temp_file = os.path.join(temp_dir, f"audio_{timestamp}.mp3")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': temp_file[:-4],  # Remove .mp3 as yt-dlp will add it
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate'
                },
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'geo_bypass': True,
                'extractor_args': {
                    'youtube': {
                        'skip_download': False,
                        'writesubtitles': False,
                        'writeautomaticsub': False
                    }
                }
            }

            self._download_with_retry(url, ydl_opts)
                
            # Verify the file exists
            final_path = temp_file
            if not os.path.exists(final_path):
                # Try without .mp3 extension
                if os.path.exists(temp_file[:-4]):
                    final_path = temp_file[:-4]
                else:
                    raise FileNotFoundError("Downloaded audio file not found")
            
            # Wait a short moment to ensure file is fully written
            time.sleep(1)
            
            return final_path
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(temp_file[:-4]):
                os.remove(temp_file[:-4])
            raise ValueError(f"Error downloading audio: {str(e)}")

    def transcribe_audio(self, audio_path):
        """Transcribe audio using Whisper model."""
        try:
            # Verify file exists and is readable
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found at {audio_path}")
            
            if os.path.getsize(audio_path) == 0:
                raise ValueError("Audio file is empty")
            
            model = self.load_model()
            result = model.transcribe(audio_path)
            
            # Clean up temporary file
            try:
                os.remove(audio_path)
            except Exception:
                pass  # Ignore cleanup errors
            
            return result["text"]
        except Exception as e:
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception:
                pass  # Ignore cleanup errors
            raise ValueError(f"Error transcribing audio: {str(e)}")

    def process_video(self, url):
        """Process video URL and return transcription."""
        audio_path = None
        try:
            audio_path = self.download_audio(url)
            if not audio_path:
                raise ValueError("Failed to download audio")
                
            transcript = self.transcribe_audio(audio_path)
            return transcript
        except Exception as e:
            # Ensure cleanup
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
            raise ValueError(f"Error processing video: {str(e)}")