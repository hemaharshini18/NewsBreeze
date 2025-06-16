import os
import base64
import logging
import re
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_html(text: str) -> str:
    """Remove HTML tags and clean text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length and add ellipsis if needed."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def format_datetime(dt_str: str) -> str:
    """Format a datetime string to a friendly format."""
    try:
        # Try different date formats common in RSS feeds
        for fmt in [
            '%a, %d %b %Y %H:%M:%S %z',  # RFC 822 format
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',       # ISO format
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ]:
            try:
                dt = datetime.strptime(dt_str.strip(), fmt)
                # Get time ago
                now = datetime.now()
                if dt.tzinfo is not None:
                    now = datetime.now(dt.tzinfo)
                    
                diff = now - dt
                
                if diff < timedelta(minutes=1):
                    return "just now"
                elif diff < timedelta(hours=1):
                    mins = diff.seconds // 60
                    return f"{mins} minute{'s' if mins > 1 else ''} ago"
                elif diff < timedelta(days=1):
                    hours = diff.seconds // 3600
                    return f"{hours} hour{'s' if hours > 1 else ''} ago"
                elif diff < timedelta(days=7):
                    days = diff.days
                    return f"{days} day{'s' if days > 1 else ''} ago"
                else:
                    return dt.strftime("%b %d, %Y")
            except ValueError:
                continue
                
        # If none of the formats match, return the original string
        return dt_str
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return dt_str

def save_to_cache(key: str, data: Any, cache_dir: str = "cache") -> bool:
    """Save data to cache file."""
    try:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{key}.json")
        
        cache_data = {
            "timestamp": time.time(),
            "data": data
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
            
        return True
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        return False

def load_from_cache(key: str, max_age_seconds: int = 3600, cache_dir: str = "cache") -> Optional[Any]:
    """Load data from cache if not expired."""
    try:
        cache_path = os.path.join(cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_path):
            return None
            
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
            
        timestamp = cache_data.get("timestamp", 0)
        data = cache_data.get("data")
        
        # Check if cache is expired
        if time.time() - timestamp > max_age_seconds:
            logger.info(f"Cache expired for key: {key}")
            return None
            
        return data
    except Exception as e:
        logger.error(f"Error loading from cache: {e}")
        return None

def get_cache_key(data: Dict[str, Any]) -> str:
    """Generate a unique cache key from data."""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

def encode_audio_for_html(audio_path: str) -> Optional[str]:
    """Encode audio file to base64 for HTML embedding."""
    try:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        return f"data:audio/wav;base64,{base64.b64encode(audio_data).decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error encoding audio: {e}")
        return None

def filter_articles_by_keywords(articles: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    """Filter articles that contain any of the given keywords."""
    if not keywords:
        return articles
        
    filtered_articles = []
    keywords_lower = [k.lower() for k in keywords]
    
    for article in articles:
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        if any(kw in title or kw in summary for kw in keywords_lower):
            filtered_articles.append(article)
            
    return filtered_articles

def sort_articles_by_date(articles: List[Dict[str, Any]], ascending: bool = False) -> List[Dict[str, Any]]:
    """Sort articles by their published date."""
    # Try to parse dates for sorting
    for article in articles:
        if 'published' in article:
            article['_sortdate'] = _parse_date(article['published'])
        else:
            article['_sortdate'] = datetime.now(timezone.utc)  # Use timezone-aware datetime
    
    # Sort articles
    sorted_articles = sorted(
        articles, 
        key=lambda x: x['_sortdate'],
        reverse=not ascending
    )
    
    # Remove temporary sorting field
    for article in sorted_articles:
        if '_sortdate' in article:
            del article['_sortdate']
            
    return sorted_articles

def _parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    try:
        # Try different date formats
        for fmt in [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                # Make sure we have a timezone-aware datetime
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
    except Exception:
        pass
        
    # Return current date as fallback (timezone-aware)
    return datetime.now(timezone.utc) 