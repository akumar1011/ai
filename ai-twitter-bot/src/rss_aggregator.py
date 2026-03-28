"""RSS feed aggregation and article processing."""

import asyncio
import random

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union

import feedparser
import requests
from loguru import logger


class RSSAggregator:
    """RSS feed aggregator for fetching and processing articles."""
    

    def __init__(self, feed_url: Union[str, List[str]]):
        """Initialize RSS aggregator.
        
        Args:

            feed_url: RSS feed URL(s) to monitor - can be a single URL string or list of URLs
        """

        if isinstance(feed_url, str):
            self.feed_urls = [feed_url]
        else:
            self.feed_urls = feed_url
        
        # Backward compatibility
        self.feed_url = self.feed_urls[0] if self.feed_urls else ""
        
        self.session = requests.Session()
        self.session.headers.update({

            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        logger.info(f"RSS Aggregator initialized with {len(self.feed_urls)} feed(s)")
    


    def select_random_feed(self) -> str:
        """Select a random RSS feed from the available feeds.
        
        Returns:
            Randomly selected RSS feed URL
        """
        if not self.feed_urls:
            raise ValueError("No RSS feeds configured")
        
        selected_feed = random.choice(self.feed_urls)
        logger.info(f"Randomly selected RSS feed: {selected_feed}")
        return selected_feed
    
    async def fetch_articles(self, limit: int = 10, use_random_feed: bool = True) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feed(s).
        
        Args:
            limit: Maximum number of articles to fetch
            use_random_feed: Whether to randomly select from available feeds
            
        Returns:
            List of article dictionaries
        """
        try:

            # Select feed URL
            if use_random_feed and len(self.feed_urls) > 1:
                feed_url = self.select_random_feed()
            else:
                feed_url = self.feed_url
            
            logger.info(f"Fetching RSS feed from {feed_url}")
            
            # Use asyncio to run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            # Add retry logic for 403 errors and other issues with different approaches
            max_retries = 4
            for attempt in range(max_retries):
                try:
                    if attempt == 0:
                        # First attempt: standard request
                        response = await loop.run_in_executor(
                            None, 
                            lambda: self.session.get(feed_url, timeout=30)
                        )
                    elif attempt == 1:
                        # Second attempt: try without some headers that might trigger blocking
                        temp_session = requests.Session()
                        temp_session.headers.update({

                            'User-Agent': 'FeedReader/1.0 (RSS Bot)',
                            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
                        })
                        response = await loop.run_in_executor(
                            None, 
                            lambda: temp_session.get(feed_url, timeout=30)
                        )
                    elif attempt == 2:
                        # Third attempt: minimal headers
                        temp_session = requests.Session()
                        temp_session.headers.update({
                            'User-Agent': 'Mozilla/5.0 (compatible; RSS Reader)'
                        })
                        response = await loop.run_in_executor(
                            None, 
                            lambda: temp_session.get(feed_url, timeout=30)
                        )
                    else:
                        # Fourth attempt: try with different encoding and headers
                        temp_session = requests.Session()
                        temp_session.headers.update({
                            'User-Agent': 'curl/7.68.0',
                            'Accept': '*/*',
                            'Accept-Encoding': 'gzip, deflate'
                        })
                        response = await loop.run_in_executor(
                            None, 
                            lambda: temp_session.get(feed_url, timeout=30)
                        )
                    
                    response.raise_for_status()
                    # Log successful request details
                    logger.info(f"Successfully fetched RSS feed from {feed_url} on attempt {attempt + 1}")
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    break  # Success, exit retry loop
                    
                except requests.exceptions.HTTPError as e:
                    if (e.response.status_code in [403, 406, 503]) and attempt < max_retries - 1:
                        logger.warning(f"HTTP {e.response.status_code} error on attempt {attempt + 1} for {feed_url}, retrying with different approach...")
                        logger.warning(f"Response headers: {dict(e.response.headers)}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"HTTP {e.response.status_code} error for {feed_url} after {max_retries} attempts")
                        logger.error(f"Response content: {e.response.text[:500]}")
                        # Log the failed URL to ensure it's captured in logs
                        logger.error(f"FAILED URL FETCH: {feed_url} - Unable to retrieve RSS feed after {max_retries} attempts")
                        raise  # Re-raise if we've exhausted retries
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Request failed on attempt {attempt + 1} for {feed_url}: {e}, retrying...")
                        logger.warning(f"Exception type: {type(e).__name__}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"All {max_retries} attempts failed for {feed_url}")
                        logger.error(f"Final exception: {type(e).__name__}: {str(e)}")
                        # Log the failed URL to ensure it's captured in logs
                        logger.error(f"FAILED URL FETCH: {feed_url} - Unable to retrieve RSS feed after {max_retries} attempts")
                        raise
            
            # Parse RSS feed with proper encoding and decompression handling
            feed = None
            try:
                # Check if content is compressed and decompress if needed
                content = response.content
                
                # Handle gzip/br compression that might not be automatically handled
                if content.startswith(b'\x01\xfc\xff') or (len(content) > 0 and content[0:3] == b'\x01\xfc\xff'):
                    pass  # TODO: Implement special handling if needed
                elif response.headers.get('content-encoding') in ['gzip', 'br', 'deflate']:
                    # Content should be automatically decompressed by requests, use text
                    content = response.text
                else:
                    # Try to decode the content with proper encoding
                    if response.encoding:
                        try:
                            content = response.content.decode(response.encoding, errors='replace')
                        except (UnicodeDecodeError, LookupError):
                            content = response.text
                    else:
                        # Try UTF-8 first, then fallback to response.text
                        try:
                            content = response.content.decode('utf-8')
                        except UnicodeDecodeError:
                            content = response.text

                # Special handling for OpenAI and other feeds that may have encoding issues
                if isinstance(content, str):
                    # Clean up potential encoding issues that cause XML parsing problems
                    import re
                    # Remove BOM if present
                    content = content.lstrip('\ufeff')
                    # Remove null bytes and other problematic characters
                    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
                    # Fix common XML encoding declaration issues
                    if content.startswith('<?xml') and 'encoding=' in content[:100]:
                        # Ensure encoding declaration matches actual content encoding
                        content = re.sub(r'encoding=["\'][^"\'>]*["\']', 'encoding="utf-8"', content, count=1)

                feed = feedparser.parse(content)
                logger.info(f"Primary RSS parsing successful for {feed_url}")
            except Exception as e:
                logger.error(f"Error decoding RSS feed content from {feed_url}: {e}")
                logger.error(f"Content encoding: {response.encoding}")
                logger.error(f"Content type: {response.headers.get('content-type', 'Unknown')}")
                logger.error(f"Content preview: {str(response.content)[:200]}...")
                logger.info(f"Attempting fallback RSS parsing methods for {feed_url}")
                
                # FALLBACK METHOD: Handle specific issues with OpenAI and other problematic feeds
                try:
                    logger.info(f"Attempting fallback RSS parsing methods for {feed_url}")
                    
                    # Method 1: Try direct feedparser with URL (bypasses our processing)
                    logger.info("Trying direct feedparser with URL...")
                    feed = feedparser.parse(feed_url)
                    
                    if feed and len(feed.entries) > 0:
                        logger.info(f"Direct URL parsing successful for {feed_url} - found {len(feed.entries)} entries")
                    else:
                        # Method 2: Try with response.text (decoded content)
                        logger.info("Trying with response.text...")
                        feed = feedparser.parse(response.text)
                        
                        if feed and len(feed.entries) > 0:
                            logger.info(f"Response text parsing successful for {feed_url} - found {len(feed.entries)} entries")
                        else:
                            # Method 3: Try with raw response.content
                            logger.info("Trying with raw response.content...")
                            feed = feedparser.parse(response.content)
                            
                            if feed and len(feed.entries) > 0:
                                logger.info(f"Raw content parsing successful for {feed_url} - found {len(feed.entries)} entries")
                            else:
                                logger.warning(f"All fallback methods failed to find entries for {feed_url}")
                        
                except Exception as fallback_error:
                    logger.error(f"Fallback RSS parsing also failed for {feed_url}: {fallback_error}")
                    # Last resort: create empty feed
                    feed = feedparser.parse('')
            
            # CRITICAL FIX: Handle feeds with malformed XML but potentially valid entries
            # Even with bozo=True, we should process the entries if they exist
            if feed and feed.bozo:
                logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
                # For feeds that return malformed XML, try alternative parsing
                if "not well-formed" in str(feed.bozo_exception) and len(feed.entries) == 0:
                    logger.info("Attempting alternative parsing for malformed XML...")
                    try:
                        # First try direct URL parsing (often works better)
                        logger.info("Trying direct feedparser URL parsing...")
                        alt_feed = feedparser.parse(feed_url)
                        if alt_feed and len(alt_feed.entries) > 0:
                            logger.info(f"Direct URL parsing found {len(alt_feed.entries)} entries!")
                            feed = alt_feed
                        else:
                            # Try to clean and re-parse the content
                            import re
                            if isinstance(content, bytes):
                                content = content.decode('utf-8', errors='replace')
                            
                            # Remove problematic characters and fix common XML issues
                            # Ensure content is string for re.sub. If it's bytes, decode first.
                            if isinstance(content, (bytes, bytearray)):
                                content_str = content.decode('utf-8', errors='replace')
                            elif isinstance(content, str):
                                content_str = content
                            else:
                                content_str = str(content)
                            cleaned_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]', '', content_str)
                            # Re-parse with cleaned content
                            feed = feedparser.parse(cleaned_content)
                            if len(feed.entries) > 0:
                                logger.info(f"Cleaned content parsing found {len(feed.entries)} entries!")
                    except Exception as e:
                        logger.warning(f"Alternative cleaning/parsing failed: {e}")
            
            # The issue is that feedparser sets bozo=True but still finds entries
            # We need to use the entries even if bozo=True
            if feed and len(feed.entries) == 0:
                logger.warning(f"No entries found in RSS feed from {feed_url}, trying alternative parsing methods...")
                logger.warning(f"Feed bozo status: {feed.bozo}")
                if feed.bozo:
                    logger.warning(f"Feed bozo exception: {feed.bozo_exception}")
                try:
                    # Try direct URL parsing first (often most reliable)
                    logger.info("Trying direct URL parsing as final attempt...")
                    feed_alt = feedparser.parse(feed_url)
                    if len(feed_alt.entries) > 0:
                        logger.info(f"Direct URL parsing found {len(feed_alt.entries)} entries!")
                        feed = feed_alt
                    else:
                        # Try parsing response.text directly
                        feed_alt = feedparser.parse(response.text)
                        if len(feed_alt.entries) > 0:
                            logger.info(f"Direct text parsing found {len(feed_alt.entries)} entries!")
                            feed = feed_alt
                        else:
                            # Try parsing response.content directly
                            feed_alt2 = feedparser.parse(response.content)
                            if len(feed_alt2.entries) > 0:
                                logger.info(f"Direct content parsing found {len(feed_alt2.entries)} entries!")
                                feed = feed_alt2
                except Exception as e:
                    logger.warning(f"Alternative parsing failed: {e}")
            
            # Ensure we have a valid feed object
            if feed is None:
                logger.error(f"Failed to parse RSS feed from {feed_url} - no valid feed object created")
                return []
            
            # Force use the feed even if it has bozo flag, as long as it has entries
            if feed.bozo and len(feed.entries) > 0:
                logger.info(f"Using bozo feed with {len(feed.entries)} entries (malformed XML but parseable)")
            elif feed.bozo and len(feed.entries) == 0:
                logger.error(f"Feed from {feed_url} has parsing errors and no entries found")
                logger.error(f"Feed bozo exception: {feed.bozo_exception}")
                return []
            
            logger.info(f"Processing {len(feed.entries)} entries from feed")

            # Debug: Show feed details
            logger.debug(f"Feed bozo: {feed.bozo}")
            logger.debug(f"Feed version: {getattr(feed, 'version', 'Unknown')}")
            if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
                logger.debug(f"Feed title: {feed.feed.title}")

            articles = []
            
            for i, entry in enumerate(feed.entries[:limit]):

                try:
                    logger.debug(f"Processing entry {i+1}: {getattr(entry, 'title', 'No Title')}")
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                        logger.debug(f"Added article: {article['title']}")
                    # No else block needed here

                except Exception as e:
                    logger.warning(f"Error parsing entry {i+1}: {e}")
                    continue
            

            logger.info(f"Successfully fetched {len(articles)} articles")
            
            # Enhanced logging and display for the fetched articles
            if articles:
                print("\n" + "="*100)
                print(f"[NEWS] FETCHED {len(articles)} ARTICLES FROM RSS FEED")
                print("="*100)
                
                for i, article in enumerate(articles, 1):
                    engagement_score = article.get('engagement_score', 0)
                    title = article.get('title', 'No Title')
                    logger.info(f"Article {i}: '{title}' - Engagement Score: {engagement_score}/10")
                
                print("\n" + "="*100)
            
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Error fetching RSS feed from {feed_url}: {e}")
            logger.error(f"Request exception details: {type(e).__name__}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_articles for {feed_url}: {e}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    def _parse_entry(self, entry: Any) -> Optional[Dict[str, Any]]:
        """Parse individual RSS entry.
        
        Args:
            entry: RSS entry object
            
        Returns:
            Parsed article dictionary or None
        """
        try:
            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.now()

            if published < datetime.now() - timedelta(days=90):
                logger.debug(f"Skipping old article: {getattr(entry, 'title', 'No Title')} (published: {published})")
                return None
            
            # Extract summary/description
            summary = ""
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description
            
            # Clean HTML tags from summary
            summary = self._clean_html(summary)
            
            # Extract tags
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
            # Extract author
            author = None
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0].get('name', '')
            
            article = {
                'title': getattr(entry, 'title', 'No Title'),
                'summary': summary,
                'link': getattr(entry, 'link', ''),
                'published': published,
                'author': author,
                'tags': tags,
                'engagement_score': self._calculate_engagement_score(entry, tags)
            }
            
            return article
            
        except Exception as e:
            logger.warning(f"Error parsing RSS entry: {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text.
        
        Args:
            text: Text with HTML tags
            
        Returns:
            Clean text without HTML tags
        """
        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def _calculate_engagement_score(self, entry: Any, tags: List[str]) -> int:
        """Calculate engagement score for an article.
        
        Args:
            entry: RSS entry object
            tags: Article tags
            
        Returns:
            Engagement score (1-10)
        """
        score = 5  # Base score
        
        # High-engagement keywords
        high_engagement_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
            'chatgpt', 'openai', 'breakthrough', 'innovation', 'future', 'revolution',
            'automation', 'robot', 'neural', 'algorithm', 'data science', 'tech',
            'startup', 'funding', 'ipo', 'acquisition', 'launch', 'release'
        ]
        
        title_lower = getattr(entry, 'title', '').lower()
        summary_lower = getattr(entry, 'summary', '').lower()
        
        # Check title for keywords
        for keyword in high_engagement_keywords:
            if keyword in title_lower:
                score += 1
                break
        
        # Check summary for keywords
        keyword_count = sum(1 for keyword in high_engagement_keywords 
                          if keyword in summary_lower)
        score += min(keyword_count, 2)
        
        # Check tags
        if tags:
            tech_tags = ['ai', 'ml', 'tech', 'startup', 'innovation']
            if any(tag.lower() in tech_tags for tag in tags):
                score += 1
        
        # Recent articles get bonus
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
            if published > datetime.now() - timedelta(hours=24):
                score += 1
        
        return min(max(score, 1), 10)  # Clamp between 1-10
    
    def select_best_article(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best article for tweeting.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Best article for tweeting
        """
        if not articles:
            raise ValueError("No articles provided")
        
        # Sort by engagement score (descending) and recency
        sorted_articles = sorted(
            articles,
            key=lambda x: (x['engagement_score'], x['published']),
            reverse=True
        )
        
        # Enhanced logging and display for article selection
        print("\n" + "="*100)
        print(f"[SELECTION] ARTICLE RANKING BY ENGAGEMENT SCORE")
        print("="*100)
        
        for i, article in enumerate(sorted_articles, 1):
            engagement_score = article.get('engagement_score', 0)
            title = article.get('title', 'No Title')
            published = article.get('published', 'Unknown')
            is_selected = i == 1
            
            if is_selected:
                print(f"   [LINK] {article.get('link', 'No Link')}")
                logger.info(f"[WINNER] SELECTED BEST ARTICLE: '{title}' - Score: {engagement_score}/10")
            # else:
            #     logger.info(f"Article #{i}: '{title}' - Score: {engagement_score}/10")
        
        print("\n" + "="*100)
        
        best_article = sorted_articles[0]
        logger.info(
            f"Selected article with engagement score {best_article['engagement_score']}: "
            f"{best_article['title']}"
        )
        
        return best_article
