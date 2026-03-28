"""Hashtag generation module with content analysis and Groq API integration."""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


from groq import Groq
from loguru import logger


class HashtagGenerator:
    """AI-powered hashtag generator for Twitter posts with content analysis."""
    
    def __init__(self, groq_api_key: str, groq_model: str, hashtag_db_path: str = "data/hashtag_database.json"):
        """Initialize hashtag generator.
        
        Args:
            groq_api_key: Groq API key for AI-powered hashtag generation
            groq_model: Groq model name to use
            hashtag_db_path: Path to hashtag database JSON file
        """
        self.groq_client = Groq(api_key=groq_api_key)
        self.groq_model = groq_model
        self.hashtag_db_path = hashtag_db_path
        self.hashtag_database = self._load_hashtag_database()
    
    def _load_hashtag_database(self) -> Dict[str, Any]:
        """Load hashtag database from JSON file.
        
        Returns:
            Hashtag database dictionary
        """
        try:
            db_path = Path(self.hashtag_db_path)
            if not db_path.exists():
                logger.warning(f"Hashtag database not found at {self.hashtag_db_path}")
                return self._get_fallback_database()
            
            with open(db_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            logger.info(f"Loaded hashtag database with {len(database.get('categories', {}))} categories")
            return database
            
        except Exception as e:
            logger.error(f"Error loading hashtag database: {e}")
            return self._get_fallback_database()
    
    def _get_fallback_database(self) -> Dict[str, Any]:
        """Get fallback hashtag database if main database fails to load.
        
        Returns:
            Basic hashtag database
        """
        return {
            "categories": {
                "ai_general": {
                    "hashtags": [
                        {"tag": "#AI", "engagement_score": 9.5, "frequency": "high"},
                        {"tag": "#MachineLearning", "engagement_score": 9.2, "frequency": "high"},
                        {"tag": "#Tech", "engagement_score": 9.4, "frequency": "high"}
                    ]
                }
            },
            "selection_rules": {
                "max_hashtags_per_tweet": 3,
                "min_engagement_score": 8.0
            }
        }
    
    async def generate_hashtags(self, tweet_content: str, article_data: Dict[str, Any]) -> List[str]:
        """Generate 2-3 high engagement hashtags for a tweet using Groq AI and database.
        
        Args:
            tweet_content: The main tweet content
            article_data: Article metadata including title, summary, link
            
        Returns:
            List of 2-3 hashtags
        """
        try:
            logger.info("Generating hashtags with content analysis")
            
            # Step 1: Analyze content and extract keywords
            content_analysis = self._analyze_content(tweet_content, article_data)
            
            # Step 2: Generate AI-powered hashtags using Groq
            ai_hashtags = await self._generate_ai_hashtags(tweet_content, article_data, content_analysis)
            
            # Step 3: Select from curated database based on content
            database_hashtags = self._select_database_hashtags(content_analysis)
            
            # Step 4: Combine and rank hashtags
            final_hashtags = self._combine_and_rank_hashtags(ai_hashtags, database_hashtags, content_analysis)
            
            # Step 5: Ensure diversity and engagement
            selected_hashtags = self._ensure_hashtag_quality(final_hashtags)
            
            logger.info(f"Generated hashtags: {selected_hashtags}")
            return selected_hashtags
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return self._get_fallback_hashtags()
    
    def _analyze_content(self, tweet_content: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tweet and article content to extract keywords and themes.
        
        Args:
            tweet_content: Tweet text
            article_data: Article metadata
            
        Returns:
            Content analysis results
        """
        try:
            # Combine all text for analysis
            full_text = f"{tweet_content} {article_data.get('title', '')} {article_data.get('summary', '')}"
            full_text = full_text.lower()
            
            # Extract keywords using content mapping
            content_mapping = self.hashtag_database.get('content_mapping', {})
            detected_categories = []
            
            for category, keywords in content_mapping.items():
                for keyword in keywords:
                    if keyword.lower() in full_text:
                        detected_categories.append(category)
                        break
            
            # Extract key phrases and technical terms
            technical_terms = re.findall(r'\b(?:AI|ML|GPT|LLM|neural|algorithm|model|data|tech|innovation)\b', full_text, re.IGNORECASE)
            
            analysis = {
                'detected_categories': list(set(detected_categories)),
                'technical_terms': list(set(technical_terms)),
                'content_length': len(tweet_content),
                'has_ai_focus': any(term in full_text for term in ['ai', 'artificial intelligence', 'machine learning', 'neural']),
                'has_tech_focus': any(term in full_text for term in ['tech', 'technology', 'innovation', 'breakthrough']),
                'has_business_focus': any(term in full_text for term in ['business', 'industry', 'enterprise', 'productivity'])
            }
            
            logger.debug(f"Content analysis: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return {'detected_categories': ['ai_general'], 'technical_terms': [], 'content_length': len(tweet_content)}
    
    async def _generate_ai_hashtags(self, tweet_content: str, article_data: Dict[str, Any], content_analysis: Dict[str, Any]) -> List[str]:
        """Generate hashtags using Groq AI based on content analysis.
        
        Args:
            tweet_content: Tweet text
            article_data: Article metadata
            content_analysis: Content analysis results
            
        Returns:
            List of AI-generated hashtags
        """
        try:
            # Create context-aware prompt
            prompt = self._create_hashtag_prompt(tweet_content, article_data, content_analysis)
            
            logger.info("Generating AI hashtags with Groq")
            
            # Use asyncio to run in thread pool since Groq client is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a social media expert specializing in high-engagement hashtag generation for AI and technology content. Generate hashtags that maximize reach and engagement."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse hashtags from AI response
            hashtags = self._parse_hashtags_from_response(ai_response)
            
            logger.info(f"AI generated {len(hashtags)} hashtags: {hashtags}")
            return hashtags
            
        except Exception as e:
            logger.error(f"Error generating AI hashtags: {e}")
            return []
    
    def _create_hashtag_prompt(self, tweet_content: str, article_data: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        """Create optimized prompt for hashtag generation.
        
        Args:
            tweet_content: Tweet text
            article_data: Article metadata
            content_analysis: Content analysis results
            
        Returns:
            Formatted prompt string
        """
        categories = ', '.join(content_analysis.get('detected_categories', ['general']))
        technical_terms = ', '.join(content_analysis.get('technical_terms', [])[:5])  # Limit to 5 terms
        
        prompt = f"""Generate 3-5 high-engagement hashtags for this AI/technology tweet:

                Tweet: "{tweet_content}"
                Article Title: "{article_data.get('title', '')}"
                Detected Categories: {categories}
                Key Technical Terms: {technical_terms}

                Requirements:
                - Maximum 3 hashtags will be selected
                - Focus on high engagement and reach
                - Mix popular and niche hashtags
                - Relevant to AI, technology, and innovation
                - Include trending hashtags when appropriate
                - Format: #HashtagName (one per line)

                Generate hashtags:"""
        
        return prompt
    
    def _parse_hashtags_from_response(self, response: str) -> List[str]:
        """Parse hashtags from AI response text.
        
        Args:
            response: AI response text
            
        Returns:
            List of parsed hashtags
        """
        try:
            # Find all hashtags in the response
            hashtags = re.findall(r'#\w+', response)
            
            # Clean and validate hashtags
            cleaned_hashtags = []
            for tag in hashtags:
                # Remove any extra characters and ensure proper format
                clean_tag = re.sub(r'[^#\w]', '', tag)
                if len(clean_tag) > 1 and clean_tag.startswith('#'):
                    cleaned_hashtags.append(clean_tag)
            
            # Remove duplicates while preserving order
            unique_hashtags = list(dict.fromkeys(cleaned_hashtags))
            
            return unique_hashtags[:5]  # Limit to 5 hashtags
            
        except Exception as e:
            logger.error(f"Error parsing hashtags: {e}")
            return []
    
    def _select_database_hashtags(self, content_analysis: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Select relevant hashtags from curated database based on content analysis.
        
        Args:
            content_analysis: Content analysis results
            
        Returns:
            List of (hashtag, engagement_score) tuples
        """
        try:
            categories = self.hashtag_database.get('categories', {})
            detected_categories = content_analysis.get('detected_categories', [])
            
            # If no categories detected, use general AI category
            if not detected_categories:
                detected_categories = ['ai_general']
            
            selected_hashtags = []
            
            # Select hashtags from detected categories
            for category_name in detected_categories:
                if category_name in categories:
                    category_hashtags = categories[category_name].get('hashtags', [])
                    
                    # Filter by engagement score
                    min_score = self.hashtag_database.get('selection_rules', {}).get('min_engagement_score', 8.0)
                    
                    for hashtag_data in category_hashtags:
                        score = hashtag_data.get('engagement_score', 0)
                        if score >= min_score:
                            selected_hashtags.append((hashtag_data['tag'], score))
            
            # Sort by engagement score (descending)
            selected_hashtags.sort(key=lambda x: x[1], reverse=True)
            
            logger.debug(f"Selected {len(selected_hashtags)} database hashtags")
            return selected_hashtags
            
        except Exception as e:
            logger.error(f"Error selecting database hashtags: {e}")
            return [("#AI", 9.5), ("#Tech", 9.4), ("#Innovation", 9.1)]
    
    def _combine_and_rank_hashtags(self, ai_hashtags: List[str], database_hashtags: List[Tuple[str, float]], content_analysis: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Combine AI and database hashtags and rank them.
        
        Args:
            ai_hashtags: AI-generated hashtags
            database_hashtags: Database hashtags with scores
            content_analysis: Content analysis results
            
        Returns:
            Ranked list of (hashtag, score) tuples
        """
        try:
            combined_hashtags = {}
            
            # Add database hashtags with their scores
            for tag, score in database_hashtags:
                combined_hashtags[tag.lower()] = (tag, score)
            
            # Add AI hashtags with estimated scores
            for tag in ai_hashtags:
                tag_lower = tag.lower()
                if tag_lower not in combined_hashtags:
                    # Estimate score based on content relevance
                    estimated_score = self._estimate_hashtag_score(tag, content_analysis)
                    combined_hashtags[tag_lower] = (tag, estimated_score)
                else:
                    # Boost score for hashtags that appear in both AI and database
                    existing_tag, existing_score = combined_hashtags[tag_lower]
                    boosted_score = min(existing_score + 0.5, 10.0)  # Cap at 10.0
                    combined_hashtags[tag_lower] = (existing_tag, boosted_score)
            
            # Convert to list and sort by score
            ranked_hashtags = list(combined_hashtags.values())
            ranked_hashtags.sort(key=lambda x: x[1], reverse=True)
            
            return ranked_hashtags
            
        except Exception as e:
            logger.error(f"Error combining hashtags: {e}")
            return [("#AI", 9.5), ("#Tech", 9.4), ("#Innovation", 9.1)]
    
    def _estimate_hashtag_score(self, hashtag: str, content_analysis: Dict[str, Any]) -> float:
        """Estimate engagement score for AI-generated hashtags.
        
        Args:
            hashtag: Hashtag to score
            content_analysis: Content analysis results
            
        Returns:
            Estimated engagement score (1-10)
        """
        try:
            base_score = 7.0  # Base score for AI-generated hashtags
            hashtag_lower = hashtag.lower()
            
            # Boost score based on relevance
            if any(term.lower() in hashtag_lower for term in content_analysis.get('technical_terms', [])):
                base_score += 1.0
            
            if content_analysis.get('has_ai_focus') and any(term in hashtag_lower for term in ['ai', 'ml', 'neural']):
                base_score += 0.8
            
            if content_analysis.get('has_tech_focus') and any(term in hashtag_lower for term in ['tech', 'innovation']):
                base_score += 0.6
            
            # Popular hashtag patterns get higher scores
            if len(hashtag) <= 10:  # Shorter hashtags tend to be more popular
                base_score += 0.3
            
            return min(base_score, 10.0)  # Cap at 10.0
            
        except Exception as e:
            logger.error(f"Error estimating hashtag score: {e}")
            return 7.0
    
    def _ensure_hashtag_quality(self, ranked_hashtags: List[Tuple[str, float]]) -> List[str]:
        """Ensure final hashtag selection meets quality and diversity requirements.
        
        Args:
            ranked_hashtags: Ranked list of (hashtag, score) tuples
            
        Returns:
            Final list of 2-3 hashtags
        """
        try:
            max_hashtags = self.hashtag_database.get('selection_rules', {}).get('max_hashtags_per_tweet', 3)
            selected = []
            
            # Select top hashtags with diversity
            used_roots = set()
            
            for hashtag, score in ranked_hashtags:
                if len(selected) >= max_hashtags:
                    break
                
                # Extract root word to ensure diversity
                root = re.sub(r'[^a-zA-Z]', '', hashtag.lower())[:6]  # First 6 chars
                
                # Avoid too similar hashtags
                if root not in used_roots or len(selected) == 0:
                    selected.append(hashtag)
                    used_roots.add(root)
            
            # Ensure we have at least 2 hashtags
            if len(selected) < 2 and len(ranked_hashtags) > 0:
                for hashtag, _ in ranked_hashtags:
                    if hashtag not in selected:
                        selected.append(hashtag)
                        if len(selected) >= 2:
                            break
            
            # Fallback if still not enough
            if len(selected) < 2:
                fallback = self._get_fallback_hashtags()
                selected.extend(fallback[:3 - len(selected)])
            
            return selected[:max_hashtags]
            
        except Exception as e:
            logger.error(f"Error ensuring hashtag quality: {e}")
            return self._get_fallback_hashtags()
    
    def _get_fallback_hashtags(self) -> List[str]:
        """Get fallback hashtags when generation fails.
        
        Returns:
            List of fallback hashtags
        """
        return ["#AI", "#Tech", "#Innovation"]
    
    def get_hashtag_stats(self) -> Dict[str, Any]:
        """Get statistics about the hashtag database.
        
        Returns:
            Database statistics
        """
        try:
            categories = self.hashtag_database.get('categories', {})
            total_hashtags = sum(len(cat.get('hashtags', [])) for cat in categories.values())
            
            stats = {
                'total_categories': len(categories),
                'total_hashtags': total_hashtags,
                'categories': list(categories.keys()),
                'database_loaded': bool(self.hashtag_database),
                'selection_rules': self.hashtag_database.get('selection_rules', {})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting hashtag stats: {e}")
            return {'error': str(e)}
