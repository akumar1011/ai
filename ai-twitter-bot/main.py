"""Main orchestrator for AI Twitter Agent - Simplified version using TwitterPoster."""

import asyncio

from pathlib import Path
from loguru import logger
import sys

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from config import config
from rss_aggregator import RSSAggregator
from content_generator import ContentGenerator
from twitter_poster import TwitterPoster
from tweet_history import TweetHistory
from hashtag_generator import HashtagGenerator

def setup_logging() -> None:
    """Setup logging configuration."""
    logger.remove()  # Remove default handler
    
    # Add file handler
    logger.add(
        config.log_file,
        level=config.log_level,
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=config.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}"
    )

async def main() -> None:
    """Main execution function - now simplified to use TwitterPoster workflow."""
    setup_logging()
    logger.info("Starting AI Twitter Agent")
    
    content_generator = None
    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully")

        # Initialize components
        rss_aggregator = RSSAggregator(config.rss_feed_urls)
        content_generator = ContentGenerator(
            groq_api_key=config.groq_api_key,
            groq_model=config.groq_model,
            ollama_base_url=config.ollama_base_url,
            ollama_model=config.ollama_model
        )
        
        # Initialize TweetHistory for duplicate detection
        tweet_history = TweetHistory(
            csv_file_path=config.tweet_history_csv,
            duplicate_days=config.duplicate_check_days
        )
        
        # Initialize HashtagGenerator for hashtag enhancement
        hashtag_generator = None
        if config.enable_hashtags:
            hashtag_generator = HashtagGenerator(
                groq_api_key=config.groq_api_key,
                groq_model=config.groq_model,
                hashtag_db_path=config.hashtag_database_path
            )
            logger.info("Hashtag generation enabled")
        else:
            logger.info("Hashtag generation disabled")
        
        # Initialize TwitterPoster with all dependencies
        twitter_poster = TwitterPoster(
            session_path=config.twitter_session_path,
            profile_dir=config.twitter_profile_dir,
            rss_aggregator=rss_aggregator,
            content_generator=content_generator,
            tweet_history=tweet_history,
            hashtag_generator=hashtag_generator
        )
        
        # Execute the complete workflow in TwitterPoster
        logger.info("Starting complete tweet generation and posting workflow")
        success = await twitter_poster.generate_and_post_complete_workflow(
            max_articles=config.max_articles_per_day
        )
        
        if success:
            logger.success("Complete workflow executed successfully!")
        else:
            logger.error("Workflow execution failed")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise
    finally:
        # Properly close async resources
        if content_generator:
            await content_generator.close()
    
    logger.info("AI Twitter Agent execution completed")

if __name__ == "__main__":
    asyncio.run(main())