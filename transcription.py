import whisper
import tempfile
import yt_dlp
import os
import time
import warnings

class TranscriptionService:
    def __init__(self):
        self.model = None

    def load_model(self, model_size="base"):
        """Load the Whisper model."""
        if self.model is None:
            # Suppress warnings about FP16
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
                self.model = whisper.load_model(model_size, device="cpu", in_memory=True)
        return self.model

    def download_audio(self, url):
        """Download audio from YouTube video using yt-dlp."""
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
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
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
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
            
            # Suppress warnings during transcription
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                result = model.transcribe(
                    audio_path,
                    fp16=False,  # Force FP32 on CPU
                    language='en'  # Specify language for better accuracy
                )
            
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