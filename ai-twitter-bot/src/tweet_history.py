"""Tweet history management for CSV operations and duplicate detection."""

import csv
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from loguru import logger



class TweetHistory:
    """Manages tweet history storage and duplicate detection.
    
    This class handles CSV operations for storing tweet history,
    checking for duplicates, and maintaining data integrity.
    """
    
    def __init__(self, csv_file_path: str, duplicate_days: int = 3):
        """Initialize tweet history manager.
        
        Args:
            csv_file_path: Path to the CSV file for storing tweet history
            duplicate_days: Number of days to check for duplicates (default: 3)
            
        Raises:
            ValueError: If duplicate_days is not positive
        """
        if duplicate_days <= 0:
            raise ValueError("duplicate_days must be positive")
            
        self.csv_file_path = Path(csv_file_path)
        self.duplicate_days = duplicate_days
        self.fieldnames = [
            'tweet_id',
            'tweet_content', 
            'article_title',
            'article_link',
            'posted_at',
            'engagement_score',
            'content_hash'
        ]
        
        # Ensure parent directory exists
        self.csv_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV file if it doesn't exist
        self._initialize_csv_file()
        
        logger.info(f"TweetHistory initialized with file: {self.csv_file_path}")
    
    def _initialize_csv_file(self) -> None:
        """Initialize CSV file with headers if it doesn't exist."""
        if not self.csv_file_path.exists():
            try:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                    writer.writeheader()
                logger.info(f"Created new CSV file: {self.csv_file_path}")
            except Exception as e:
                logger.error(f"Error creating CSV file: {e}")
                raise
    
    def _generate_content_hash(self, tweet_content: str) -> str:
        """Generate a hash for tweet content for quick duplicate detection.
        
        Args:
            tweet_content: Tweet text content
            
        Returns:
            Hash string for the content
        """
        import hashlib

        import re
        # Normalize content: lowercase, remove extra spaces, remove URLs
        normalized = re.sub(r'http[s]?://\S+', '', tweet_content.lower())
        normalized = ' '.join(normalized.split())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:

        """Calculate basic similarity between two text strings.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on key terms and concepts.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Keyword similarity ratio between 0.0 and 1.0
        """
        import re
        
        # Extract meaningful keywords (remove common words, emojis, hashtags)
        def extract_keywords(text):
            # Remove URLs, mentions, hashtags, emojis
            cleaned = re.sub(r'http[s]?://\S+|@\w+|#\w+|[^\w\s]', ' ', text.lower())
            
            # Common stop words to remove
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
                'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            
            words = [word for word in cleaned.split() if word and len(word) > 2 and word not in stop_words]
            return set(words)
        
        keywords1 = extract_keywords(text1)
        keywords2 = extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_normalized_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity after normalizing text (removing emojis, hashtags, etc.).
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Normalized similarity ratio between 0.0 and 1.0
        """
        import re
        
        def normalize_text(text):
            # Remove emojis, hashtags, mentions, URLs, and special characters
            normalized = re.sub(r'[🔥🚀💡🤖⚡️✨🌟💻🎯📱🛠️🎨🔧⭐️🎪🎭🎬🎤🎵🎶🎸🎹🎺🎻🥁🎲🎯🎪🎨🖼️🖌️🖍️✏️📝📄📃📑📊📈📉📋📌📍📎📏📐✂️📇📅📆🗓️📇📋📊📈📉📋]', '', text)
            normalized = re.sub(r'#\w+|@\w+|http[s]?://\S+', '', normalized)
            normalized = re.sub(r'[^\w\s]', ' ', normalized)
            normalized = ' '.join(normalized.split())  # Remove extra spaces
            return normalized.lower().strip()
        
        norm1 = normalize_text(text1)
        norm2 = normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def save_tweet(self, tweet_data: Dict[str, Any]) -> bool:
        """Save a posted tweet to the CSV file.
        
        Args:
            tweet_data: Dictionary containing tweet information with keys:
                       - tweet_content: The actual tweet text
                       - article_title: Title of the source article
                       - article_link: Link to the source article
                       - engagement_score: Predicted engagement score
                       - tweet_id: Optional unique identifier
                       
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate required fields
            required_fields = ['tweet_content', 'article_title', 'article_link']
            for field in required_fields:
                if field not in tweet_data or not tweet_data[field]:
                    raise ValueError(f"Required field '{field}' is missing or empty")
            
            # Prepare tweet record
            tweet_record = {
                'tweet_id': tweet_data.get('tweet_id', self._generate_tweet_id()),
                'tweet_content': tweet_data['tweet_content'].strip(),
                'article_title': tweet_data['article_title'].strip(),
                'article_link': tweet_data['article_link'].strip(),
                'posted_at': datetime.now().isoformat(),
                'engagement_score': tweet_data.get('engagement_score', 0),
                'content_hash': self._generate_content_hash(tweet_data['tweet_content'])
            }
            
            # Append to CSV file
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writerow(tweet_record)
            
            logger.info(f"Tweet saved to history: {tweet_record['tweet_id']}")
            logger.info(f"Tweet content: {tweet_data['tweet_content'][:50]}...")
            logger.info(f"Article link: {tweet_data['article_link']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tweet to history: {e}")
            return False
    
    def _generate_tweet_id(self) -> str:
        """Generate a unique tweet ID.
        
        Returns:
            Unique tweet identifier
        """
        import uuid
        return f"tweet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def load_recent_tweets(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load tweets from the last N days.
        
        Args:
            days: Number of days to look back (defaults to self.duplicate_days)
            
        Returns:
            List of tweet dictionaries from the specified period
        """
        if days is None:
            days = self.duplicate_days
            
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_tweets = []
        
        try:
            if not self.csv_file_path.exists():
                return recent_tweets
                
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        posted_at = datetime.fromisoformat(row['posted_at'])
                        if posted_at >= cutoff_date:
                            recent_tweets.append(row)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing tweet record: {e}")
                        continue
            
            logger.info(f"Loaded {len(recent_tweets)} tweets from last {days} days")
            return recent_tweets
            
        except Exception as e:
            logger.error(f"Error loading recent tweets: {e}")
            return []
    


    def is_duplicate(self, tweet_content: str, article_link: str = None, similarity_threshold: float = 0.75) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if tweet content is a duplicate of recent tweets with enhanced detection.
        
        Args:
            tweet_content: Tweet content to check
            article_link: Optional article link to check for link-based duplicates
            similarity_threshold: Minimum similarity ratio to consider duplicate (0.0-1.0)
            
        Returns:
            Tuple of (is_duplicate: bool, matching_tweet: Optional[Dict])
        """
        try:
            # Validate input
            if not tweet_content or not isinstance(tweet_content, str):
                raise ValueError("tweet_content must be a non-empty string")
                
            if not 0.0 <= similarity_threshold <= 1.0:
                raise ValueError("similarity_threshold must be between 0.0 and 1.0")
            
            # Generate hash for quick exact match check
            content_hash = self._generate_content_hash(tweet_content)
            
            # Load recent tweets
            recent_tweets = self.load_recent_tweets()
            
            if not recent_tweets:
                logger.info("No recent tweets found, content is not a duplicate")
                return False, None
            

            # Enhanced duplicate detection with multiple strategies
            
            # Strategy 1: Exact hash matches (fastest)
            for tweet in recent_tweets:
                if tweet.get('content_hash') == content_hash:
                    logger.info(f"Exact duplicate found: {tweet['tweet_id']}")
                    return True, tweet
            

            # Strategy 2: Link-based duplicate detection (if article_link provided)
            if article_link:
                for tweet in recent_tweets:
                    if tweet.get('article_link') == article_link:
                        logger.info(f"Same article link found: {tweet['tweet_id']} - {article_link}")
                        return True, tweet
            
            # Strategy 3: Enhanced semantic similarity with multiple checks
            for tweet in recent_tweets:


                # Basic text similarity
                basic_similarity = self._calculate_similarity(tweet_content, tweet['tweet_content'])
                
                # Keyword-based similarity (extract key terms)
                keyword_similarity = self._calculate_keyword_similarity(tweet_content, tweet['tweet_content'])
                
                # Normalized similarity (remove common words, emojis, hashtags)
                normalized_similarity = self._calculate_normalized_similarity(tweet_content, tweet['tweet_content'])
                
                # Combined similarity score (weighted average)
                combined_similarity = (
                    basic_similarity * 0.4 + 
                    keyword_similarity * 0.3 + 
                    normalized_similarity * 0.3
                )
                
                # Check if any similarity metric exceeds threshold
                if (basic_similarity >= similarity_threshold or 
                    keyword_similarity >= 0.85 or  # Higher threshold for keywords
                    normalized_similarity >= 0.8 or  # Higher threshold for normalized
                    combined_similarity >= similarity_threshold):
                    
                    logger.info(

                        f"Similar tweet found - Basic: {basic_similarity:.2f}, "
                        f"Keyword: {keyword_similarity:.2f}, Normalized: {normalized_similarity:.2f}, "
                        f"Combined: {combined_similarity:.2f} - Tweet: {tweet['tweet_id']}"
                    )
                    return True, tweet
            
            logger.info("No duplicate tweets found")
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            # In case of error, assume not duplicate to avoid blocking tweets
            return False, None
    
    def get_tweet_statistics(self) -> Dict[str, Any]:
        """Get statistics about tweet history.
        
        Returns:
            Dictionary containing tweet statistics
        """
        try:
            if not self.csv_file_path.exists():
                return {
                    'total_tweets': 0,
                    'recent_tweets': 0,
                    'avg_engagement_score': 0.0,
                    'oldest_tweet': None,
                    'newest_tweet': None
                }
            
            all_tweets = []
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        row['posted_at'] = datetime.fromisoformat(row['posted_at'])
                        row['engagement_score'] = float(row.get('engagement_score', 0))
                        all_tweets.append(row)
                    except (ValueError, KeyError):
                        continue
            
            if not all_tweets:
                return {
                    'total_tweets': 0,
                    'recent_tweets': 0,
                    'avg_engagement_score': 0.0,
                    'oldest_tweet': None,
                    'newest_tweet': None
                }
            
            recent_tweets = self.load_recent_tweets()
            
            # Calculate statistics
            engagement_scores = [tweet['engagement_score'] for tweet in all_tweets]
            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
            
            sorted_tweets = sorted(all_tweets, key=lambda x: x['posted_at'])
            
            return {
                'total_tweets': len(all_tweets),
                'recent_tweets': len(recent_tweets),
                'avg_engagement_score': round(avg_engagement, 2),
                'oldest_tweet': sorted_tweets[0]['posted_at'].isoformat() if sorted_tweets else None,
                'newest_tweet': sorted_tweets[-1]['posted_at'].isoformat() if sorted_tweets else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {
                'total_tweets': 0,
                'recent_tweets': 0,
                'avg_engagement_score': 0.0,
                'oldest_tweet': None,
                'newest_tweet': None,
                'error': str(e)
            }
    
    def cleanup_old_tweets(self, keep_days: int = 30) -> int:
        """Remove tweets older than specified days to manage file size.
        
        Args:
            keep_days: Number of days of tweets to keep
            
        Returns:
            Number of tweets removed
        """
        try:
            if not self.csv_file_path.exists():
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            kept_tweets = []
            removed_count = 0
            
            # Read all tweets
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        posted_at = datetime.fromisoformat(row['posted_at'])
                        if posted_at >= cutoff_date:
                            kept_tweets.append(row)
                        else:
                            removed_count += 1
                    except (ValueError, KeyError):
                        # Keep malformed records to avoid data loss
                        kept_tweets.append(row)
            
            # Rewrite file with only recent tweets
            if removed_count > 0:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                    writer.writeheader()
                    writer.writerows(kept_tweets)
                
                logger.info(f"Cleaned up {removed_count} old tweets, kept {len(kept_tweets)}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
