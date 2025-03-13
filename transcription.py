import whisper
import tempfile
import yt_dlp
import os
import random
import time
import requests
import json
from urllib.parse import urlparse

class ProxyManager:
    """Manages a pool of proxy servers and rotates them."""
    def __init__(self):
        # Free proxy list - replace with your paid proxy service in production
        self.proxy_list = [
            None,  # Direct connection
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080',
        ]
        self.current_index = 0

    def get_next_proxy(self):
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy

class UserAgentManager:
    """Manages and rotates user agents."""
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

    def get_random_user_agent(self):
        return random.choice(self.user_agents)

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.proxy_manager = ProxyManager()
        self.user_agent_manager = UserAgentManager()
        self.download_methods = [
            self._download_with_ytdlp,
            self._download_with_requests,
        ]

    def load_model(self, model_size="base"):
        """Load the Whisper model."""
        if self.model is None:
            self.model = whisper.load_model(model_size, device="cpu", in_memory=True)
        return self.model

    def _get_cookie_path(self):
        """Get path to cookies file, create if doesn't exist."""
        cookie_dir = os.path.join(os.path.expanduser("~"), ".yt-dlp")
        os.makedirs(cookie_dir, exist_ok=True)
        return os.path.join(cookie_dir, "cookies.txt")

    def _download_with_ytdlp(self, url, temp_file, proxy=None, max_retries=3, initial_delay=1):
        """Attempt download with exponential backoff retry."""
        last_exception = None
        delay = initial_delay
        cookie_path = self._get_cookie_path()
        user_agent = self.user_agent_manager.get_random_user_agent()

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': temp_file[:-4],
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookie_path,
            'user_agent': user_agent,
            'headers': {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            },
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'geo_bypass': True,
        }

        if proxy:
            ydl_opts['proxy'] = proxy

        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return True
            except Exception as e:
                last_exception = e
                if "HTTP Error 403" not in str(e):
                    raise e  # Re-raise if it's not a 403 error

                # Add jitter to delay
                jitter = random.uniform(0, 0.1) * delay
                time.sleep(delay + jitter)
                delay *= 2  # Exponential backoff

        if last_exception:
            raise last_exception

    def _download_with_requests(self, url, temp_file, proxy=None, max_retries=3):
        """Fallback download method using requests."""
        session = requests.Session()
        if proxy:
            session.proxies = {'http': proxy, 'https': proxy}

        headers = {
            'User-Agent': self.user_agent_manager.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Range': 'bytes=0-',
        }

        response = session.get(url, headers=headers, stream=True)
        response.raise_for_status()

        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def download_audio(self, url):
        """Download audio from YouTube video using yt-dlp."""
        temp_file = None
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            time.sleep(random.uniform(0.1, 0.5))  # Add small random delay before request
            temp_file = os.path.join(temp_dir, f"audio_{timestamp}.mp3")
            last_error = None

            # Try each proxy in rotation
            for _ in range(3):  # Try up to 3 different proxies
                proxy = self.proxy_manager.get_next_proxy()
                
                # Try each download method
                for download_method in self.download_methods:
                    try:
                        download_method(url, temp_file, proxy)
                        # If download succeeds, break both loops
                        if os.path.exists(temp_file):
                            return temp_file
                    except Exception as e:
                        last_error = e
                        continue

            if last_error:
                raise last_error

            if not os.path.exists(temp_file):
                raise FileNotFoundError("Downloaded audio file not found")

            return temp_file

        except Exception as e:
            if temp_file:
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