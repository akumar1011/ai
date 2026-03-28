"""AI content generation using Groq and Ollama."""

import asyncio
import re
from typing import Dict, Any

import httpx
from groq import Groq
from loguru import logger

from config import config

class ContentGenerator:
    """AI content generator for creating engaging tweets."""
    
    def __init__(
        self, 
        groq_api_key: str, 
        groq_model: str,
        ollama_base_url: str,
        ollama_model: str
    ):
        """Initialize content generator.
        
        Args:
            groq_api_key: Groq API key
            groq_model: Groq model name
            ollama_base_url: Ollama server URL
            ollama_model: Ollama model name
        """
        self.groq_client = Groq(api_key=groq_api_key)
        self.groq_model = groq_model
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.ollama_model = ollama_model
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def calculate_tweet_engagement_score(self, tweet: str, article: Dict[str, Any]) -> float:
        """Calculate engagement score for a tweet based on various factors.
        
        Args:
            tweet: Tweet content to score
            article: Source article for context
            
        Returns:
            Engagement score (1.0-10.0)
        """
        try:
            base_score = 5.0  # Base engagement score
            tweet_lower = tweet.lower()
            
            # High-engagement keywords and phrases
            engagement_keywords = [
                'breakthrough', 'revolutionary', 'game-changing', 'innovative', 'cutting-edge',
                'amazing', 'incredible', 'stunning', 'remarkable', 'groundbreaking',
                'future', 'next-level', 'transform', 'disrupt', 'advance',
                'ai', 'artificial intelligence', 'machine learning', 'deep learning',
                'chatgpt', 'openai', 'google', 'microsoft', 'tesla', 'nvidia'
            ]
            
            # Action words that drive engagement
            action_words = [
                'discover', 'learn', 'explore', 'see', 'watch', 'check out',
                'find out', 'revealed', 'announced', 'launched', 'released'
            ]
            
            # Score based on keyword presence
            keyword_count = sum(1 for keyword in engagement_keywords if keyword in tweet_lower)
            base_score += min(keyword_count * 0.5, 2.0)  # Max 2 points for keywords
            
            # Score based on action words
            action_count = sum(1 for word in action_words if word in tweet_lower)
            base_score += min(action_count * 0.3, 1.0)  # Max 1 point for action words
            
            # Emotional triggers
            emotional_words = [
                'excited', 'thrilled', 'fascinated', 'impressed', 'shocked',
                'surprised', 'mind-blowing', 'unbelievable', 'wow'
            ]
            
            # Score based on emotional triggers
            emotion_count = sum(1 for word in emotional_words if word in tweet_lower)
            base_score += min(emotion_count * 0.4, 1.5)  # Max 1.5 points for emotions
            
            # Length optimization (Twitter sweet spot: 120-160 characters)
            tweet_length = len(tweet)
            if 120 <= tweet_length <= 160:
                base_score += 1.0  # Optimal length bonus
            elif 100 <= tweet_length <= 180:
                base_score += 0.5  # Good length bonus
            elif tweet_length > 200:
                base_score -= 0.5  # Too long penalty
            
            # Question format bonus (drives engagement)
            if '?' in tweet:
                base_score += 0.5
            
            # Exclamation point bonus (shows excitement)
            exclamation_count = tweet.count('!')
            base_score += min(exclamation_count * 0.2, 0.6)  # Max 0.6 for exclamations
            
            # Numbers and statistics bonus (concrete information)
            numbers = re.findall(r'\d+', tweet)
            if numbers:
                base_score += min(len(numbers) * 0.3, 1.0)  # Max 1 point for numbers
            
            # Article engagement score influence
            article_score = article.get('engagement_score', 5)
            base_score += (article_score - 5) * 0.1  # Slight influence from article score
            
            # Clamp score between 1.0 and 10.0
            final_score = max(1.0, min(base_score, 10.0))
            
            logger.debug(f"Tweet engagement score calculated: {final_score:.2f} for tweet: {tweet}")
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating tweet engagement score: {e}")
            return 5.0  # Default score on error
    
    async def generate_tweet_groq(self, article: Dict[str, Any]) -> str:
        """Generate initial tweet using Groq API.
        
        Args:
            article: Article dictionary with title, summary, link
            
        Returns:
            Generated tweet text
        """
        try:
            prompt = self._create_tweet_prompt(article)
            
            logger.info("Generating tweet with Groq API")
            
            # Use asyncio to run in thread pool since Groq client is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media manager who creates viral, engaging tweets about AI and technology. Your tweets are informative, exciting, and drive high engagement."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
            )
            
            tweet = response.choices[0].message.content.strip()
            



            # Enhanced quote removal for Groq responses
            # Remove leading and trailing quotes (both single and double)
            while tweet.startswith('"') or tweet.startswith("'"):
                tweet = tweet[1:]
            while tweet.endswith('"') or tweet.endswith("'"):
                tweet = tweet[:-1]
            
            # Remove any remaining leading/trailing whitespace after quote removal
            tweet = tweet.strip()
            
            # Handle edge case where Groq might return quoted content with labels
            if ':' in tweet and tweet.count(':') == 1:
                parts = tweet.split(':', 1)
                if len(parts) == 2 and len(parts[0]) < 20:  # Likely a label like "Tweet:"
                    tweet = parts[1].strip()
                    # Remove quotes again after extracting content
                    while tweet.startswith('"') or tweet.startswith("'"):
                        tweet = tweet[1:]
                    while tweet.endswith('"') or tweet.endswith("'"):
                        tweet = tweet[:-1]
                    tweet = tweet.strip()
            
            logger.info(f"Groq generated tweet: {tweet}")
            return tweet
            
        except Exception as e:
            logger.error(f"Error generating tweet with Groq: {e}")
            # Fallback to simple tweet
            return f"Exciting AI breakthrough: {article.get('title', 'New development')}"
    
    async def polish_tweet_ollama(self, initial_tweet: str) -> str:
        try:
            logger.info("Polishing tweet with Ollama")
            
            prompt = f"""Polish this tweet to make it more engaging and human-like while keeping it under {config.max_tweet_length} characters. Make it sound natural and conversational, but maintain the key information. Do NOT add any emojis.

            IMPORTANT: Respond with ONLY the polished tweet text. Do not include explanations, introductions, or any additional text.

            Original tweet: {initial_tweet}

            Polished tweet:"""
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "max_tokens": 100
                }
            }
            
            response = await self.http_client.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            polished_tweet = result.get('response', '').strip()
            
            # Enhanced quote handling to prevent double quotes at the beginning
            # First, handle common Ollama response patterns

            if polished_tweet.startswith('Here is a polished version'):
                # Find the actual tweet in quotes
                start_quote = polished_tweet.find('"')
                end_quote = polished_tweet.find('"', start_quote + 1)
                if start_quote != -1 and end_quote != -1:
                    polished_tweet = polished_tweet[start_quote + 1:end_quote]
            
            # Remove any remaining explanatory text after the tweet
            lines = polished_tweet.split('\n')
            if lines:
                polished_tweet = lines[0].strip()
            
            # Comprehensive quote removal - handle all quote variations
            # Remove leading and trailing quotes (both single and double)
            while polished_tweet.startswith('"') or polished_tweet.startswith("'"):
                polished_tweet = polished_tweet[1:]
            while polished_tweet.endswith('"') or polished_tweet.endswith("'"):
                polished_tweet = polished_tweet[:-1]
            
            # Remove any remaining leading/trailing whitespace after quote removal
            polished_tweet = polished_tweet.strip()
            
            # Handle edge case where Ollama might return quoted content in different formats
            # Check for patterns like: "Tweet: content" or "Polished: content"
            if ':' in polished_tweet and polished_tweet.count(':') == 1:
                parts = polished_tweet.split(':', 1)
                if len(parts) == 2 and len(parts[0]) < 20:  # Likely a label
                    polished_tweet = parts[1].strip()
                    # Remove quotes again after extracting content
                    while polished_tweet.startswith('"') or polished_tweet.startswith("'"):
                        polished_tweet = polished_tweet[1:]
                    while polished_tweet.endswith('"') or polished_tweet.endswith("'"):
                        polished_tweet = polished_tweet[:-1]
                    polished_tweet = polished_tweet.strip()
            
            if not polished_tweet:
                logger.warning("Ollama returned empty response, using original tweet")
                return initial_tweet
            
            logger.info(f"Ollama polished tweet: {polished_tweet}")
            return polished_tweet

            
        except Exception as e:
            logger.error(f"Error polishing tweet with Ollama: {e}")
            return initial_tweet  # Fallback to original
    
    def _create_tweet_prompt(self, article: Dict[str, Any]) -> str:
        """Create prompt for tweet generation.
        
        Args:
            article: Article dictionary
            
        Returns:
            Formatted prompt string
        """
        return f"""Create an engaging Twitter post about this article:

Summary: {article['summary'][:300]}...

- Maximum {config.max_tweet_length - 40} characters (to leave space for the actual link that will be added separately)
- Make it sound exciting and worth reading
- Do NOT add any emojis

- CRITICAL: Do NOT include any link, URL, or link placeholders like [link], (link), "Read more", etc.
- CRITICAL: Write complete hashtags - never truncate hashtags with dots (...)
- End with complete hashtags, not partial ones
Tweet:"""
    

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
