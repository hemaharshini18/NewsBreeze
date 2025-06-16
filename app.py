import streamlit as st
import os
import logging
import time
from datetime import datetime
import base64
from typing import Dict, List, Any, Optional, Tuple

# Import dotenv with error handling
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    # Continue without .env file

# Import custom modules
from news_fetcher import NewsFetcher
from summarizer import ArticleSummarizer
from voice_generator import VoiceGenerator
import utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create necessary directories
os.makedirs("cache", exist_ok=True)
os.makedirs("audio_cache", exist_ok=True)
os.makedirs("assets/voices", exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="NewsBreeze",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .article-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #333;
    }
    .article-meta {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .article-summary {
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
    .article-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .audio-player {
        width: 100%;
        margin-top: 0.5rem;
    }
    .article-source {
        font-size: 0.8rem;
        color: #1E88E5;
    }
    .source-tag {
        background-color: #E3F2FD;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_news(
    sources: Dict[str, str] = None, 
    max_articles: int = 5,
    keywords: List[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch news articles and cache the result."""
    fetcher = NewsFetcher(feeds=sources)
    all_news = fetcher.fetch_all_feeds(max_articles_per_feed=max_articles)
    
    # Filter by keywords if provided
    if keywords:
        filtered_news = {}
        for source, articles in all_news.items():
            filtered_articles = utils.filter_articles_by_keywords(articles, keywords)
            if filtered_articles:
                filtered_news[source] = filtered_articles
        return filtered_news
    
    return all_news

@st.cache_data(ttl=600)
def summarize_articles(articles: List[Dict[str, Any]], use_api: bool = False) -> List[Dict[str, Any]]:
    """Summarize list of articles and cache the results."""
    summarizer = ArticleSummarizer(use_api=use_api)
    return summarizer.summarize_articles(articles)

def generate_audio_for_article(article: Dict[str, Any], voice_name: str) -> Optional[str]:
    """Generate audio for an article with selected voice."""
    voice_gen = VoiceGenerator()
    return voice_gen.generate_audio_for_article(article, voice_name)

def display_article_card(article: Dict[str, Any], index: int, selected_voice: str):
    """Display a single article card with audio player."""
    with st.container():
        st.markdown(f"""
        <div class="article-card">
            <div class="article-source">
                <span class="source-tag">{article.get('source_name', 'News')}</span>
            </div>
            <div class="article-title">{article.get('title', 'No title')}</div>
            <div class="article-meta">
                Published: {utils.format_datetime(article.get('published', ''))}
            </div>
        """, unsafe_allow_html=True)
        
        # Display AI summary if available
        if 'ai_summary' in article:
            st.markdown(f"""
            <div class="article-summary">
                <strong>AI Summary:</strong> {article['ai_summary']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="article-summary">
                {utils.truncate_text(article.get('summary', 'No summary available'), 250)}
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Generate and play audio
            if st.button(f"🔊 Read with {selected_voice}", key=f"btn_read_{index}"):
                with st.spinner("Generating audio..."):
                    audio_path = generate_audio_for_article(article, selected_voice)
                    
                    if audio_path and os.path.exists(audio_path):
                        # Store the audio path in session state
                        st.session_state[f"audio_{index}"] = audio_path
                        st.experimental_rerun()
            
            # Display audio player if audio has been generated
            if f"audio_{index}" in st.session_state:
                audio_path = st.session_state[f"audio_{index}"]
                try:
                    with open(audio_path, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.error(f"Error playing audio: {e}")
        
        with col2:
            if article.get('link'):
                st.markdown(f"[Read full article]({article['link']})")
        
        st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Initialize session state if needed
    if 'fetched_news' not in st.session_state:
        st.session_state.fetched_news = {}
    if 'summarized_articles' not in st.session_state:
        st.session_state.summarized_articles = []
    if 'selected_sources' not in st.session_state:
        st.session_state.selected_sources = []
    
    # Header
    st.markdown('<h1 class="main-header">📰 NewsBreeze</h1>', unsafe_allow_html=True)
    st.markdown("### Your AI-Powered Audio News Reader")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Voice selection
        voice_gen = VoiceGenerator()
        available_voices = voice_gen.get_available_voices()
        selected_voice = st.selectbox(
            "Select Voice",
            available_voices,
            index=0 if available_voices else 0,
            key="voice_selector"
        )
        
        # News source selection
        st.subheader("News Sources")
        
        # Default news sources
        default_sources = NewsFetcher.DEFAULT_FEEDS
        
        # Allow selecting from available sources
        selected_sources = {}
        for source_name, source_url in default_sources.items():
            if st.checkbox(source_name, value=True, key=f"src_{source_name}"):
                selected_sources[source_name] = source_url
        
        # Article limit
        article_limit = st.slider(
            "Articles per source",
            min_value=1,
            max_value=10,
            value=3,
            step=1
        )
        
        # Keyword filtering
        st.subheader("Filter Articles")
        keywords_input = st.text_input("Keywords (comma separated)")
        keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []
        
        # Option to use HF API for summarization
        use_api = st.checkbox("Use Hugging Face API for summarization", value=False)
        
        # Refresh button
        if st.button("🔄 Refresh News"):
            with st.spinner("Fetching latest news..."):
                try:
                    # Clear cache to force refresh
                    fetch_news.clear()
                    summarize_articles.clear()
                    
                    # Fetch and process news
                    st.session_state.fetched_news = fetch_news(
                        sources=selected_sources,
                        max_articles=article_limit,
                        keywords=keywords
                    )
                    
                    # Check if we got any news
                    if not st.session_state.fetched_news:
                        st.warning("No news articles were found. This might be due to RSS feed issues or network problems.")
                        st.session_state.summarized_articles = []
                        return
                    
                    # Process all articles from all sources
                    all_articles = []
                    for source, articles in st.session_state.fetched_news.items():
                        for article in articles:
                            # Add source name to each article
                            article['source_name'] = source
                            all_articles.append(article)
                    
                    st.info(f"Found {len(all_articles)} articles from {len(st.session_state.fetched_news)} sources")
                    
                    # Sort by date (newest first)
                    all_articles = utils.sort_articles_by_date(all_articles)
                    
                    # Summarize articles
                    if all_articles:
                        st.session_state.summarized_articles = summarize_articles(all_articles, use_api=use_api)
                    else:
                        st.warning("No articles found to summarize.")
                        st.session_state.summarized_articles = []
                    
                except Exception as e:
                    import traceback
                    st.error(f"Error fetching or processing news: {str(e)}")
                    st.error(f"Details: {traceback.format_exc()}")
        
        # Add information about the app
        st.markdown("---")
        st.markdown("""
        ### About NewsBreeze
        
        - Fetches news from RSS feeds
        - Summarizes using AI (Falconsai/text_summarization)
        - Reads articles aloud using Google TTS
        """)
    
    # Main content area
    if not st.session_state.summarized_articles:
        st.info("👈 Select news sources and click 'Refresh News' to get started!")
        
        # Sample view for first-time users
        st.markdown("### Sample Article View")
        with st.container():
            st.markdown("""
            <div class="article-card">
                <div class="article-source">
                    <span class="source-tag">Sample News</span>
                </div>
                <div class="article-title">Welcome to NewsBreeze: AI-Powered News Reader</div>
                <div class="article-meta">
                    Published: Just now
                </div>
                <div class="article-summary">
                    <strong>AI Summary:</strong> NewsBreeze combines the latest news headlines with AI summarization and audio reading capabilities. Select your news sources from the sidebar and click "Refresh News" to get started.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Display the articles
        for i, article in enumerate(st.session_state.summarized_articles):
            display_article_card(article, i, selected_voice)
        
        # Show message if no articles are found
        if len(st.session_state.summarized_articles) == 0:
            st.warning("No articles found with the current settings. Try adjusting your filters or adding more sources.")

if __name__ == "__main__":
    main() 