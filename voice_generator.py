import os
import logging
import time
from typing import Dict, Optional, List
import hashlib
from gtts import gTTS
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Class to generate speech from text using Google Text-to-Speech."""
    
    # Available voices with their corresponding language codes
    AVAILABLE_VOICES = {
        "English (US Female)": {"lang": "en", "tld": "com"},
        "English (UK Female)": {"lang": "en", "tld": "co.uk"},
        "English (US Male)": {"lang": "en", "tld": "us"},
        "French": {"lang": "fr", "tld": "fr"},
        "German": {"lang": "de", "tld": "de"},
        "Spanish": {"lang": "es", "tld": "es"},
        "Italian": {"lang": "it", "tld": "it"}
    }
    
    def __init__(self, cache_dir: str = "audio_cache"):
        """
        Initialize the voice generator.
        
        Args:
            cache_dir: Directory to cache generated audio files
        """
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info("Voice generator initialized with Google TTS")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices."""
        return list(self.AVAILABLE_VOICES.keys())
    
    def generate_audio(self, text: str, voice_name: str, language: str = "en") -> Optional[str]:
        """
        Generate audio from text using Google TTS.
        
        Args:
            text: The text to convert to speech
            voice_name: Name of the voice to use
            language: Language code (default: "en")
            
        Returns:
            Path to the generated audio file or None if failed
        """
        if not text:
            logger.warning("Cannot generate audio for empty text")
            return None
            
        # Generate a cache key based on the text and voice
        cache_key = hashlib.md5(f"{text}_{voice_name}_{language}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        # Check if we already have this audio cached
        if os.path.exists(cache_path):
            logger.info(f"Using cached audio for '{text[:30]}...' with voice {voice_name}")
            return cache_path
            
        # Get voice settings
        voice_settings = self.AVAILABLE_VOICES.get(voice_name, {"lang": "en", "tld": "com"})
        
        try:
            # Generate speech using gTTS
            tts = gTTS(
                text=text, 
                lang=voice_settings["lang"], 
                tld=voice_settings["tld"],
                slow=False
            )
            
            # Save to file
            tts.save(cache_path)
            
            logger.info(f"Successfully generated audio saved to {cache_path}")
            return cache_path
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
    
    def text_to_chunks(self, text: str, max_chars: int = 500) -> List[str]:
        """
        Split text into chunks for better TTS processing.
        
        Args:
            text: Text to split
            max_chars: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        # Simple sentence splitting
        sentences = []
        for sent in text.replace("!", ".").replace("?", ".").split("."):
            sent = sent.strip()
            if sent:
                sentences.append(sent + ".")
                
        # Combine sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def generate_audio_for_article(self, article: Dict, voice_name: str, language: str = "en") -> Optional[str]:
        """
        Generate audio for an article.
        
        Args:
            article: Article dictionary with ai_summary field
            voice_name: Name of the voice to use
            language: Language code
            
        Returns:
            Path to the generated audio file or None if failed
        """
        # Get the text to convert to speech (use AI summary if available)
        text = article.get("ai_summary", article.get("summary", article.get("title", "")))
        
        if not text:
            logger.warning("No text available for TTS generation")
            return None
        
        # Limit text length to avoid issues with very long articles
        if len(text) > 3000:
            text = text[:3000] + "..."
            
        # Generate audio
        return self.generate_audio(text, voice_name, language)

# Example usage
if __name__ == "__main__":
    # Example
    vg = VoiceGenerator()
    
    print("Available voices:", vg.get_available_voices())
    
    # Example text
    text = "Hello, this is a test of the text-to-speech system."
    
    # Try to generate audio with a voice
    audio_path = vg.generate_audio(text, "English (US Female)")
    
    if audio_path:
        print(f"Audio generated successfully at: {audio_path}")
    else:
        print("Audio generation failed.") 