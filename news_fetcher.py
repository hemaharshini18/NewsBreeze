import feedparser
import requests
from typing import List, Dict, Any
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsFetcher:
    """Class to fetch news from various RSS feeds."""
    
    # Default list of common news RSS feeds (updated with more reliable feeds)
    DEFAULT_FEEDS = {
        "BBC News": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition_world.rss",
        "Reuters": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "NPR": "https://feeds.npr.org/1001/rss.xml",
        "ABC News": "https://abcnews.go.com/abcnews/topstories",
        "USA Today": "http://rssfeeds.usatoday.com/UsatodaycomWorld-TopStories",
        "Yahoo News": "https://news.yahoo.com/rss"
    }
    
    def __init__(self, feeds: Dict[str, str] = None):
        """Initialize with a dictionary of feeds (name: url)."""
        self.feeds = feeds or self.DEFAULT_FEEDS
    
    def fetch_all_feeds(self, max_articles_per_feed: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch articles from all feeds."""
        all_articles = {}
        
        for source_name, feed_url in self.feeds.items():
            try:
                articles = self.fetch_feed(feed_url, max_articles_per_feed)
                if articles:
                    all_articles[source_name] = articles
                    logger.info(f"Retrieved {len(articles)} articles from {source_name}")
                else:
                    logger.warning(f"No articles retrieved from {source_name}")
            except Exception as e:
                logger.error(f"Error fetching feed {source_name}: {e}")
        
        return all_articles
    
    def fetch_feed(self, feed_url: str, max_articles: int = 5) -> List[Dict[str, Any]]:
        """Fetch articles from a specific feed URL."""
        try:
            logger.info(f"Fetching feed from: {feed_url}")
            
            # Add user agent to avoid 403 errors
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsBreeze/1.0'}
            
            # Use requests to get the feed content
            try:
                response = requests.get(feed_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # Parse the feed content
                logger.info(f"Successfully got response from {feed_url}, parsing content...")
                feed = feedparser.parse(response.content)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {feed_url}: {e}")
                # Try direct parsing without requests
                logger.info(f"Trying direct parsing for {feed_url}")
                feed = feedparser.parse(feed_url)
            
            # Check if feed parsing was successful
            if not feed:
                logger.warning(f"Feed parsing failed for: {feed_url}")
                return []
                
            if not feed.get('entries'):
                logger.warning(f"No entries found in feed: {feed_url}")
                # Debug feed structure
                logger.debug(f"Feed keys: {feed.keys()}")
                return []
            
            logger.info(f"Found {len(feed.entries)} entries in feed {feed_url}")
            
            # Process and return the entries
            articles = []
            for entry in feed.entries[:max_articles]:
                try:
                    # Extract the required fields
                    article = {
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', entry.get('pubDate', 'No date')),
                        'summary': entry.get('summary', entry.get('description', 'No summary available')),
                        'source_url': feed_url
                    }
                    articles.append(article)
                except Exception as entry_error:
                    logger.error(f"Error processing entry in {feed_url}: {entry_error}")
            
            logger.info(f"Successfully processed {len(articles)} articles from {feed_url}")
            return articles
        
        except Exception as e:
            logger.error(f"Error processing feed {feed_url}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def add_feed(self, name: str, url: str) -> bool:
        """Add a new feed to the list of feeds."""
        try:
            # Test if the feed is valid
            test = self.fetch_feed(url, 1)
            if test:
                self.feeds[name] = url
                return True
            return False
        except Exception:
            return False
    
    def remove_feed(self, name: str) -> bool:
        """Remove a feed from the list of feeds."""
        if name in self.feeds:
            del self.feeds[name]
            return True
        return False

# Example usage
if __name__ == "__main__":
    fetcher = NewsFetcher()
    news = fetcher.fetch_all_feeds(3)
    
    for source, articles in news.items():
        print(f"\n{source} - {len(articles)} articles:")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"   Published: {article['published']}")
            print(f"   Link: {article['link']}")
            print(f"   Summary: {article['summary'][:100]}...") 