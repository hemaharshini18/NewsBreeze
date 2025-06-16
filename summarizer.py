import logging
import os
import requests
import time
from typing import Dict, Any, Optional, List
from transformers import pipeline
import re
from html import unescape
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArticleSummarizer:
    """Class to summarize news articles using Hugging Face models."""
    
    def __init__(self, model_name: str = "Falconsai/text_summarization", use_api: bool = False):
        """Initialize with a specific summarization model."""
        self.model_name = model_name
        self.use_api = use_api
        self.api_token = os.environ.get("HUGGINGFACE_API_TOKEN")
        
        # Initialize the model if not using API
        if not use_api:
            try:
                logger.info(f"Loading summarization model: {model_name}")
                # Check if CUDA is available
                device = 0 if torch.cuda.is_available() else -1
                self.summarizer = pipeline("summarization", model=model_name, device=device)
                logger.info(f"Model loaded successfully on device: {device}")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                logger.warning("Falling back to API mode")
                self.use_api = True
    
    def clean_text(self, text: str) -> str:
        """Clean HTML and normalize text for better summarization."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = unescape(text)
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 30) -> Optional[str]:
        """Summarize the given text."""
        if not text:
            return None
        
        # Clean the text
        text = self.clean_text(text)
        
        # Check if text is too short to summarize
        if len(text.split()) < min_length:
            return text
        
        try:
            if self.use_api:
                return self._summarize_with_api(text, max_length, min_length)
            else:
                return self._summarize_with_pipeline(text, max_length, min_length)
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            # Return a truncated version of the original text as fallback
            return text[:max_length*2] + "..." if len(text) > max_length*2 else text
    
    def _summarize_with_pipeline(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """Summarize using the local pipeline."""
        result = self.summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        
        return result[0]['summary_text']
    
    def _summarize_with_api(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """Summarize using the Hugging Face API."""
        if not self.api_token:
            logger.warning("No API token provided. Using fallback method.")
            return text[:max_length*2] + "..." if len(text) > max_length*2 else text
        
        API_URL = f"https://api-inference.huggingface.co/models/{self.model_name}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": False
            }
        }
        
        # Retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                if isinstance(result, list) and result:
                    return result[0].get('summary_text', text)
                else:
                    # If API returns unexpected format
                    logger.warning(f"Unexpected API response format: {result}")
                    return text
            except requests.exceptions.RequestException as e:
                logger.error(f"API request error (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2)  # Wait before retrying
        
        # Fallback if all retries failed
        return text[:max_length*2] + "..." if len(text) > max_length*2 else text
    
    def summarize_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarize a list of articles."""
        summarized_articles = []
        
        for article in articles:
            # Get the text to summarize (either summary or full content)
            text_to_summarize = article.get('summary', '')
            
            # If no summary is available or it's too short, try to get full content
            # Note: In a real app, you'd fetch the full article here if needed
            
            # Summarize the text
            summary = self.summarize_text(text_to_summarize)
            
            # Create a new article dict with the summary
            summarized_article = article.copy()
            summarized_article['ai_summary'] = summary
            
            summarized_articles.append(summarized_article)
        
        return summarized_articles

# Example usage
if __name__ == "__main__":
    # Test with a sample article
    sample_text = """
    The European Union has agreed to open membership talks with Ukraine, in a major boost to President Volodymyr Zelensky. 
    Leaders of the 27 EU nations made the historic decision at a summit in Brussels. 
    Mr Zelensky hailed the agreement as a "victory" for his country and for "all of Europe". 
    Hungary's prime minister, Viktor Orban, had threatened to veto the decision but left the room when the decision was made. 
    The announcement comes just days after the US Congress blocked a major package of military assistance for Ukraine in its war with Russia.
    """
    
    summarizer = ArticleSummarizer(use_api=False)  # Try with local model first
    summary = summarizer.summarize_text(sample_text)
    
    print("Original text:", sample_text)
    print("\nSummarized text:", summary) 