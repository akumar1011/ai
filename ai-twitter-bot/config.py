"""Configuration management for AI Twitter Agent."""

from datetime import datetime
import os
from typing import Optional, List
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables

load_dotenv(override=True)

class Config:
    """Configuration class for the AI Twitter Agent."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # AI API Configuration
        self.groq_api_key: str = self._get_required_env("GROQ_API_KEY")
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        
        # Ollama Configuration
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # RSS Feed Configuration
        self.rss_feed_urls: List[str] = [
            "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "https://www.reddit.com/r/MachineLearning/.rss",
            "https://www.reddit.com/r/artificial/.rss",
            "https://openai.com/news/rss.xml",
            "https://blog.google/technology/ai/rss/",
            "https://huggingface.co/blog/feed.xml",
            "https://rss.arxiv.org/rss/cs.AI",
            "https://bair.berkeley.edu/blog/feed.xml",
            "https://venturebeat.com/category/ai/feed/",
            "https://www.artificialintelligence-news.com/feed/",
            "https://www.wired.com/feed/tag/ai/latest/rss"
        ]
        # Backward compatibility
        self.rss_feed_url: str = os.getenv(
            "RSS_FEED_URL", 
            "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
        )
        self.max_articles_per_day: int = int(os.getenv("MAX_ARTICLES_PER_DAY", "5"))
        
        # Twitter Configuration
        self.twitter_session_path: str = os.getenv(
            "TWITTER_SESSION_PATH", 
            "twitter_profile/twitter_session.json"
        )
        self.twitter_profile_dir: str = os.getenv(
            "TWITTER_PROFILE_DIR", 
            "twitter_profile"
        )
        
        # Posting Schedule
        self.post_time_hour: int = int(os.getenv("POST_TIME_HOUR", "10"))
        self.post_time_minute: int = int(os.getenv("POST_TIME_MINUTE", "30"))
        self.random_delay_minutes: int = int(os.getenv("RANDOM_DELAY_MINUTES", "60"))
        
        # Content Settings
        self.max_tweet_length: int = int(os.getenv("MAX_TWEET_LENGTH", "280"))
        self.min_engagement_score: int = int(os.getenv("MIN_ENGAGEMENT_SCORE", "7"))
        
        # Logging
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        log_file = f"agent.{timestamp}.log"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_file: str = os.getenv("LOG_FILE", f"logs/{log_file}")
        
        # Tweet History Configuration
        self.tweet_history_csv: str = os.getenv(
            "TWEET_HISTORY_CSV", 
            "data/tweet_history.csv"
        )
        self.duplicate_check_days: int = int(os.getenv("DUPLICATE_CHECK_DAYS", "3"))
        
        # Hashtag Configuration
        self.hashtag_database_path: str = os.getenv(
            "HASHTAG_DATABASE_PATH", 
            "data/hashtag_database.json"
        )
        self.enable_hashtags: bool = os.getenv("ENABLE_HASHTAGS", "true").lower() == "true"
        self.max_hashtags_per_tweet: int = int(os.getenv("MAX_HASHTAGS_PER_TWEET", "3"))
        
        # Create necessary directories
        self._create_directories()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error.
        
        Args:
            key: Environment variable key
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            Path(self.twitter_profile_dir),
            Path(self.log_file).parent,
            Path(self.tweet_history_csv).parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration settings.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate time settings
        if not (0 <= self.post_time_hour <= 23):
            raise ValueError("POST_TIME_HOUR must be between 0 and 23")
        
        if not (0 <= self.post_time_minute <= 59):
            raise ValueError("POST_TIME_MINUTE must be between 0 and 59")
        
        # Validate content settings
        if self.max_tweet_length > 280:
            raise ValueError("MAX_TWEET_LENGTH cannot exceed 280 characters")
        
        if not (1 <= self.min_engagement_score <= 10):
            raise ValueError("MIN_ENGAGEMENT_SCORE must be between 1 and 10")
        
        return True

# Global configuration instance
config = Config()