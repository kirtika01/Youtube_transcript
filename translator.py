from deep_translator import GoogleTranslator
from typing import Dict, Optional
import time

class TranslationService:
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh-cn': 'Chinese (Simplified)',
            'hi': 'Hindi',
            'ar': 'Arabic',
            'bn': 'Bengali',
            'ur': 'Urdu',
            'te': 'Telugu',
            'ta': 'Tamil',
            'mr': 'Marathi',
            'gu': 'Gujarati'
        }
        # Map some language codes to what deep-translator expects
        self.lang_code_map = {
            'zh-cn': 'zh-CN',
            'bn': 'bn',
            'gu': 'gu',
            'mr': 'mr',
            'te': 'te',
            'ta': 'ta',
            'ur': 'ur'
        }

    def get_supported_languages(self) -> Dict[str, str]:
        """Return dictionary of supported languages."""
        return self.supported_languages

    def translate_text(self, text: Optional[str], target_lang: str) -> str:
        """
        Translate text to target language.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
            
        Raises:
            ValueError: If text is None or empty, or if language is not supported
        """
        try:
            if not text or not isinstance(text, str):
                raise ValueError("Invalid input: text must be a non-empty string")

            text = text.strip()
            if not text:
                raise ValueError("Invalid input: text contains only whitespace")

            if target_lang not in self.supported_languages:
                raise ValueError(f"Language code '{target_lang}' not supported")

            # If target language is English and text is not None, return original text
            if target_lang == 'en':
                return text

            # Map language code if necessary
            translated_target_lang = self.lang_code_map.get(target_lang, target_lang)

            # Split text into smaller chunks if it's too long (deep_translator has a limit)
            MAX_CHUNK_LENGTH = 4999  # Google Translate API limit is 5000 characters
            chunks = [text[i:i + MAX_CHUNK_LENGTH] for i in range(0, len(text), MAX_CHUNK_LENGTH)]
            
            translated_chunks = []
            translator = GoogleTranslator(source='auto', target=translated_target_lang)
            
            for chunk in chunks:
                # Add a small delay between chunks to avoid rate limiting
                if len(chunks) > 1:
                    time.sleep(0.5)
                    
                translated_text = translator.translate(text=chunk)
                if not translated_text:
                    raise ValueError("Translation produced no result")
                translated_chunks.append(translated_text)

            return ' '.join(translated_chunks)

        except Exception as e:
            raise ValueError(f"Translation error: {str(e)}")

    def detect_language(self, text: Optional[str]) -> str:
        """
        Detect the language of the given text.
        
        Args:
            text (str): Text to detect language from
            
        Returns:
            str: Detected language code
            
        Raises:
            ValueError: If text is None or empty
        """
        try:
            if not text or not isinstance(text, str):
                raise ValueError("Invalid input: text must be a non-empty string")

            text = text.strip()
            if not text:
                raise ValueError("Invalid input: text contains only whitespace")

            translator = GoogleTranslator(source='auto', target='en')
            detected_lang = translator.detect(text)
            return detected_lang.lower()

        except Exception as e:
            raise ValueError(f"Language detection error: {str(e)}")