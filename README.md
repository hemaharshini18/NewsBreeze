# NewsBreeze

NewsBreeze is a news aggregation application that fetches the latest headlines, summarizes them using AI, and reads them aloud using text-to-speech technology.

## Features

- Fetches latest news headlines from RSS feeds
- Summarizes articles using Hugging Face's summarization models (Falconsai/text_summarization)
- Reads headlines aloud using Google Text-to-Speech in multiple languages and accents
- Clean and intuitive UI for browsing news and playing audio

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/NewsBreeze.git
   cd NewsBreeze
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with your API keys:
   ```
   # Optional: Your Hugging Face API token if you plan to use the API instead of local models
   HUGGINGFACE_API_TOKEN=your_token_here
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

## Models Used

- **Text Summarization**: Falconsai/text_summarization - A Hugging Face model for abstractive text summarization
- **Text-to-Speech**: Google TTS (gTTS) - Text-to-Speech API for multiple languages and accents

## Project Structure

- `app.py`: Main Streamlit application
- `news_fetcher.py`: Module for fetching news from RSS feeds
- `summarizer.py`: Module for article summarization using Hugging Face models
- `voice_generator.py`: Module for generating audio using XTTS v2
- `utils.py`: Utility functions

## Note

Voice cloning technology should only be used for ethical purposes and with proper consent. This app is for educational purposes only. 