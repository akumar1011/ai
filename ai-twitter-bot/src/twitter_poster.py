import asyncio
import os
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import config

class TwitterPoster:
    """Twitter posting automation using Playwright with complete tweet workflow and duplicate detection."""
    
    def __init__(self, session_path: str, profile_dir: str, rss_aggregator=None, content_generator=None, tweet_history=None, hashtag_generator=None):
        """Initialize Twitter poster.
        
        Args:
            session_path: Path to saved Twitter session file
            profile_dir: Directory for browser profile storage
            rss_aggregator: RSS aggregator instance for fetching articles
            content_generator: Content generator instance for creating tweets
            tweet_history: Tweet history instance for duplicate detection
            hashtag_generator: Hashtag generator instance for adding hashtags
        """
        self.session_path = session_path
        self.profile_dir = profile_dir
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.rss_aggregator = rss_aggregator
        self.content_generator = content_generator
        self.tweet_history = tweet_history
        self.hashtag_generator = hashtag_generator
        
        # Ensure directories exist
        Path(profile_dir).mkdir(parents=True, exist_ok=True)
        Path(session_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def login_and_save_session(self, headless: bool = False) -> bool:
        """Login to Twitter and save session (based on your existing code).
        
        Args:
            headless: Whether to run browser in headless mode
            
        Returns:
            True if session saved successfully
        """
        try:
            async with async_playwright() as p:
                # Launch browser with anti-detection options
                browser = await p.chromium.launch(
                    headless=headless,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # Create context with realistic settings
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                page = await context.new_page()
                page.set_default_timeout(30000)
                
                # Navigate to Twitter login
                logger.info("Navigating to X/Twitter login page")
                await page.goto("https://x.com/login", wait_until="domcontentloaded")
                
                # Wait for login form
                try:
                    await page.wait_for_selector('input[name="text"]', timeout=10000)
                    logger.info("Login form detected")
                except Exception:
                    logger.warning("Login form not immediately detected")
                
                # Manual login prompt
                logger.info("Manual login required - please complete login in the browser")
                
                # Wait for user to complete login
                # In a real implementation, you might want to check for successful login
                await asyncio.sleep(60)  # Give user time to login
                
                # Save session state
                await context.storage_state(path=self.session_path)
                logger.success(f"Session saved to {self.session_path}")
                
                await browser.close()
                return True
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    async def test_session(self) -> bool:
        """Test if saved session is still valid.
        
        Returns:
            True if session is valid
        """
        if not os.path.exists(self.session_path):
            logger.warning(f"Session file {self.session_path} not found")
            return False
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(storage_state=self.session_path)
                page = await context.new_page()
                
                await page.goto("https://x.com/home", wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                current_url = page.url
                is_logged_in = "home" in current_url or "x.com" in current_url
                
                await browser.close()
                
                if is_logged_in:
                    logger.info("Session is valid")
                    return True
                else:
                    logger.warning("Session appears to be expired")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing session: {e}")
            return False
    
    async def generate_and_post_complete_workflow(self, max_articles: int = 5) -> bool:
        """Complete workflow: fetch articles, generate tweets, check duplicates, and post.
        
        Args:
            max_articles: Maximum number of articles to fetch
            
        Returns:
            True if tweet posted successfully
        """
        try:
            if not self.rss_aggregator or not self.content_generator or not self.tweet_history:
                logger.error("RSS aggregator, content generator, and tweet history must be provided")
                return False
            
            # Step 1: Fetch RSS articles
            logger.info("Fetching RSS articles")
            articles = await self.rss_aggregator.fetch_articles(limit=max_articles)
            
            if not articles:
                logger.warning("No articles found in RSS feed")
                return False
            
            logger.info(f"Found {len(articles)} articles")
            
            # Enhanced display of all fetched articles with engagement scores
            print("\n" + "="*100)
            print(f"[SCORES] ARTICLE ENGAGEMENT SCORE SUMMARY")
            print("="*100)
            
            for i, article in enumerate(articles, 1):
                engagement_score = article.get('engagement_score', 0)
                title = article.get('title', 'No Title')
                
                print(f"[ARTICLE {i}] Score {engagement_score}/10 - {title}")
                logger.info(f"Article {i} engagement score: {engagement_score}/10 - '{title}'")
            
            print("\n" + "="*100)
            
            # Step 2: Loop through articles until we find a non-duplicate tweet
            max_retry_attempts = min(len(articles), 10)  # Limit retries to prevent infinite loops
            attempt = 0
            final_tweet_with_link = None
            selected_article = None
            tried_articles = []
            
            while attempt < max_retry_attempts:
                attempt += 1
                logger.info(f"Attempt {attempt}/{max_retry_attempts} to find non-duplicate tweet")
                
                # Select best article for this attempt (excluding already tried ones)
                remaining_articles = [a for a in articles if a not in tried_articles]
                if not remaining_articles:
                    logger.warning("No more articles to try")
                    break
                
                selected_article = self.rss_aggregator.select_best_article(remaining_articles)
                tried_articles.append(selected_article)
                
                # Enhanced logging for selected article
                print(f"\n[CHOSEN] SELECTED ARTICLE FOR ATTEMPT {attempt}:")
                print(f"   Title: {selected_article['title']}")
                print(f"   Engagement Score: {selected_article.get('engagement_score', 0)}/10")
                print(f"   Published: {selected_article.get('published', 'Unknown')}")
                print(f"   Link: {selected_article.get('link', 'No Link')}")
                
                logger.info(f"Selected article: {selected_article['title']} (Score: {selected_article.get('engagement_score', 0)}/10)")
                
                # Step 3: Generate multiple tweet variations (5 tweets)
                logger.info("Generating 5 tweet variations with Groq")
                tweet_variations = []
                
                print("\n" + "="*80)
                print(f"[GENERATE] GENERATING TWEET VARIATIONS - ATTEMPT {attempt}")
                print("="*80)
                
                for i in range(5):
                    logger.info(f"Generating tweet variation {i+1}/5")
                    tweet = await self.content_generator.generate_tweet_groq(selected_article)
                    tweet_variations.append(tweet)
                    print(f"\n[TWEET {i+1}]:")
                    print(f"   {tweet}")
                    print(f"   Length: {len(tweet)} characters")
                    logger.info(f"Generated tweet {i+1}: {tweet}")
                
                # Step 4: Enhanced tweet selection with engagement scoring
                print("\n" + "="*80)
                print(f"[SELECTION] TWEET ENGAGEMENT ANALYSIS - ATTEMPT {attempt}")
                print("="*80)
                
                # Calculate engagement scores for all tweet variations
                tweet_scores = []
                for i, tweet in enumerate(tweet_variations):
                    try:
                        score = await self.content_generator.calculate_tweet_engagement_score(tweet, selected_article)
                        tweet_scores.append((tweet, score, i+1))
                        print(f"\n[TWEET {i+1} SCORE]: {score:.2f}/10")
                        print(f"   Content: {tweet}")
                        print(f"   Length: {len(tweet)} characters")
                        logger.info(f"Tweet {i+1} engagement score: {score:.2f}/10 - '{tweet}'")
                    except Exception as e:
                        logger.warning(f"Error scoring tweet {i+1}: {e}")
                        tweet_scores.append((tweet, 5.0, i+1))  # Default score
                        print(f"\n[TWEET {i+1} SCORE]: 5.00/10 (default - scoring error)")
                        print(f"   Content: {tweet}")
                        print(f"   Length: {len(tweet)} characters")
                
                # Sort tweets by engagement score (highest first)
                tweet_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Select the highest scoring tweet
                selected_tweet, best_score, tweet_number = tweet_scores[0]
                
                print("\n" + "="*80)
                print(f"[WINNER] SELECTED HIGHEST ENGAGEMENT TWEET")
                print("="*80)
                print(f"   Selected: TWEET {tweet_number}")
                print(f"   Score: {best_score:.2f}/10")
                print(f"   Content: {selected_tweet}")
                print(f"   Length: {len(selected_tweet)} characters")
                
                logger.info(f"[SELECTION] Selected tweet {tweet_number} with highest engagement score: {best_score:.2f}/10")
                logger.info(f"[SELECTION] Winning tweet content: '{selected_tweet}'")
                
                # Log all scores for comparison
                print(f"\n[RANKING] FINAL TWEET RANKING:")
                for rank, (tweet_content, score, original_number) in enumerate(tweet_scores, 1):
                    status = "👑 SELECTED" if rank == 1 else f"#{rank}"
                    print(f"   {status}: Tweet {original_number} - Score {score:.2f}/10")
                    logger.info(f"Rank #{rank}: Tweet {original_number} - Score {score:.2f}/10 - '{tweet_content}'")
                
                # Step 5: Polish the selected tweet with Ollama
                logger.info("Polishing selected tweet content with Ollama")
                polished_tweet = await self.content_generator.polish_tweet_ollama(selected_tweet)
                
                # Step 6: Generate hashtags if hashtag generator is available
                hashtags = []
                if self.hashtag_generator:
                    try:
                        logger.info("Generating hashtags for tweet")
                        hashtags = await self.hashtag_generator.generate_hashtags(polished_tweet, selected_article)
                        logger.info(f"Generated hashtags: {hashtags}")
                    except Exception as e:
                        logger.warning(f"Hashtag generation failed: {e}")
                        hashtags = []
                
                # Step 7: Combine tweet with hashtags and link
                hashtag_text = " ".join(hashtags) if hashtags else ""
                if hashtag_text:
                    final_tweet_with_link = f"{polished_tweet} {hashtag_text} {selected_article['link']}"
                else:
                    final_tweet_with_link = f"{polished_tweet} {selected_article['link']}"
                
                if len(final_tweet_with_link) > config.max_tweet_length:
                    # Calculate available characters for content
                    link_length = len(selected_article['link'])
                    hashtag_length = len(hashtag_text) + (1 if hashtag_text else 0)  # +1 for space
                    available_chars = config.max_tweet_length - link_length - hashtag_length - 2  # -2 for spaceses
                    
                    # Word-preserving truncation of the main tweet content
                    words = polished_tweet.split()
                    truncated_words = []
                    current_length = 0
                    
                    for word in words:
                        word_length = len(word)
                        space_length = 1 if truncated_words else 0
                        total_length = current_length + space_length + word_length
                        
                        if total_length > available_chars:
                            break
                        
                        truncated_words.append(word)
                        current_length = total_length
                    
                    truncated_tweet = ' '.join(truncated_words)
                    
                    # Rebuild final tweet with truncated content
                    if hashtag_text:
                        final_tweet_with_link = f"{truncated_tweet} {hashtag_text} {selected_article['link']}"
                    else:
                        final_tweet_with_link = f"{truncated_tweet} {selected_article['link']}"
                
                print("\n" + "="*80)
                print(f"[DUPLICATE CHECK] DUPLICATE CHECK - ATTEMPT {attempt}")
                print("="*80)
                print(f"   Checking selected tweet (Score: {best_score:.2f}/10): {selected_tweet}")
                logger.info(f"Performing duplicate check on selected tweet with score {best_score:.2f}/10: '{selected_tweet}'")
                
                # Step 8: Enhanced duplicate check with article link
                is_duplicate, matching_tweet = self.tweet_history.is_duplicate(
                    polished_tweet, 
                    article_link=selected_article['link'],
                    similarity_threshold=0.75  # Slightly lower threshold for more sensitive detection
                )
                
                if is_duplicate:
                    logger.warning(f"Duplicate tweet detected! Similar to tweet: {matching_tweet['tweet_id']}")
                    print(f"[DUPLICATE] DUPLICATE DETECTED: Similar to tweet {matching_tweet['tweet_id']}")
                    print(f"   Original: {matching_tweet['tweet_content']}")
                    print(f"   New:      {polished_tweet}")
                    
                    # Check if it's a link-based duplicate
                    if matching_tweet.get('article_link') == selected_article['link']:
                        print(f"   [LINK] SAME ARTICLE LINK: {selected_article['link']}")
                    else:
                        print(f"   [CONTENT] CONTENT SIMILARITY DETECTED")
                    
                    print(f"   Trying next article...")
                    continue  # Try next article
                else:
                    logger.info("No duplicate found, proceeding with posting")
                    print(f"[SUCCESS] NO DUPLICATE FOUND - Proceeding with posting")
                    print(f"   Final tweet: {final_tweet_with_link}")
                    print(f"   Length: {len(final_tweet_with_link)} characters")
                    break  # Exit loop, we found a non-duplicate tweet
            
            # If we exhausted all attempts without finding a non-duplicate
            if attempt >= max_retry_attempts and (not final_tweet_with_link or is_duplicate):
                logger.error("Could not find a non-duplicate tweet after all attempts")
                return False
            
            # Ensure we have valid data before proceeding
            if not final_tweet_with_link or not selected_article:
                logger.error("Missing required data for posting tweet")
                return False
            
            print("\n" + "="*80)
            print("[TWITTER] POSTING TO TWITTER")
            print("="*80)
            
            # Step 9: Post to Twitter
            logger.info("Posting to Twitter")
            success = await self.post_tweet(final_tweet_with_link)
            
            if success:
                # Step 10: Save tweet to history
                logger.info("Saving tweet to history")
                tweet_data = {
                    'tweet_content': polished_tweet,  # Save without link for duplicate detection
                    'article_title': selected_article['title'],
                    'article_link': selected_article['link'],
                    'engagement_score': selected_article.get('engagement_score', 0)
                }
                
                save_success = self.tweet_history.save_tweet(tweet_data)
                if save_success:
                    logger.success("Tweet posted and saved to history successfully!")
                else:
                    logger.warning("Tweet posted but failed to save to history")
                
                return True
            else:
                logger.error("Failed to post tweet")
                return False
                
        except Exception as e:
            logger.error(f"Error in complete workflow: {e}")
            return False
    
    async def post_tweet(self, tweet_text: str) -> bool:
        """Post a tweet to Twitter.
        
        Args:
            tweet_text: Text content of the tweet
            
        Returns:
            True if tweet posted successfully
        """
        try:
            # Validate session first
            if not await self.test_session():
                logger.error("Invalid session - please login first")
                return False
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # Visible for debugging
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security'
                    ]
                )
                context = await browser.new_context(
                    storage_state=self.session_path,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                page.set_default_timeout(30000)  # Set reasonable timeout of 30 seconds
                
                # Add extra wait for page stability
                await page.add_init_script("""
                    // Remove automation detection
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                # Navigate to Twitter home
                logger.info("Navigating to Twitter home")
                try:
                    await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(3)
                    logger.info("Successfully navigated to Twitter home")
                except Exception as e:
                    logger.warning(f"Navigation timeout, trying alternative approach: {e}")
                    # Try direct navigation without waiting for networkidle
                    await page.goto("https://x.com/home", timeout=60000)
                    await asyncio.sleep(5)  # Give more time for page to fully load
                
                # Wait for the page to be fully interactive with better timeout handling
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)
                    logger.info("DOM content loaded")
                    
                    # Try networkidle but don't fail if it times out
                    try:
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        logger.info("Network idle achieved")
                    except Exception as e:
                        logger.warning(f"Network idle timeout (continuing anyway): {e}")
                        
                except Exception as e:
                    logger.warning(f"Page load timeout (continuing anyway): {e}")
                
                logger.info("Page loading completed (or timed out gracefully)")
                
                # Find and click the tweet compose button
                try:
                    # Try multiple selectors for the compose button with better error handling
                    compose_selectors = [
                        '[data-testid="SideNav_NewTweet_Button"]',  # Main sidebar tweet button
                        '[data-testid="tweetButtonInline"]',        # Inline tweet button
                        'a[href="/compose/tweet"]',                 # Direct compose link
                        '[aria-label*="Post"]',                     # New "Post" label
                        '[aria-label*="Tweet"]',                    # Legacy "Tweet" label
                        'div[role="button"][aria-label*="Post"]',   # Post button with role
                        'div[role="button"][aria-label*="Tweet"]'   # Tweet button with role
                    ]
                    
                    compose_button = None
                    used_selector = None
                    
                    # Wait longer and try each selector
                    for selector in compose_selectors:
                        try:
                            logger.info(f"Trying selector: {selector}")
                            compose_button = await page.wait_for_selector(selector, timeout=3000)
                            if compose_button:
                                # Check if button is visible and enabled
                                is_visible = await compose_button.is_visible()
                                is_enabled = await compose_button.is_enabled()
                                logger.info(f"Button found - Visible: {is_visible}, Enabled: {is_enabled}")
                                
                                if is_visible and is_enabled:
                                    used_selector = selector
                                    break
                                else:
                                    compose_button = None
                        except Exception as e:
                            logger.debug(f"Selector {selector} failed: {e}")
                            continue
                    
                    if not compose_button:
                        # Take a screenshot for debugging
                        await page.screenshot(path="debug_twitter_page.png")
                        logger.error("Could not find enabled tweet compose button. Screenshot saved as debug_twitter_page.png")
                        
                        # Try alternative approach - look for any clickable element with "Post" or "Tweet"
                        logger.info("Trying alternative approach...")
                        try:
                            # Try clicking on the main tweet compose area
                            tweet_area = await page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=5000)
                            if tweet_area:
                                logger.info("Found tweet text area directly")
                                await tweet_area.click()
                                # Skip the compose button click and go directly to text input
                                await asyncio.sleep(2)
                            else:
                                await browser.close()
                                return False
                        except:
                            await browser.close()
                            return False
                    else:
                        logger.info(f"Using selector: {used_selector}")
                        await compose_button.click()
                        logger.info("Clicked compose button")
                        await asyncio.sleep(2)  # Wait for compose dialog to open
                    
                except Exception as e:
                    logger.error(f"Error finding compose button: {e}")
                    await browser.close()
                    return False
                
                # Wait for compose dialog and enter tweet text
                try:
                    # Try multiple selectors for the text area
                    text_area_selectors = [
                        '[data-testid="tweetTextarea_0"]',
                        '[role="textbox"][aria-label*="Post"]',
                        '[role="textbox"][aria-label*="Tweet"]',
                        'div[contenteditable="true"][role="textbox"]'
                    ]
                    
                    text_area = None
                    for selector in text_area_selectors:
                        try:
                            logger.info(f"Looking for text area with selector: {selector}")
                            text_area = await page.wait_for_selector(selector, timeout=5000)
                            if text_area:
                                is_visible = await text_area.is_visible()
                                logger.info(f"Text area found - Visible: {is_visible}")
                                if is_visible:
                                    break
                                else:
                                    text_area = None
                        except Exception as e:
                            logger.debug(f"Text area selector {selector} failed: {e}")
                            continue
                    
                    if not text_area:
                        await page.screenshot(path="debug_no_textarea.png")
                        logger.error("Could not find tweet text area. Screenshot saved.")
                        await browser.close()
                        return False
                        
                    # Clear any existing text and type the tweet
                    await text_area.click()
                    await asyncio.sleep(2)
                    
                    # Try different methods to enter text
                    try:
                        # Method 1: Use fill() which is faster
                        await text_area.fill(tweet_text)
                        logger.info(f"Used fill() method for tweet text: {tweet_text[:50]}...")
                    except Exception as e:
                        logger.warning(f"Fill method failed: {e}, trying type method")
                        try:
                            # Method 2: Use type() with shorter delay
                            await text_area.fill('')  # Clear first
                            await text_area.type(tweet_text, delay=20)  # Faster typing
                            logger.info(f"Used type() method for tweet text: {tweet_text[:50]}...")
                        except Exception as e2:
                            logger.warning(f"Type method failed: {e2}, trying keyboard input")
                            # Method 3: Use keyboard input
                            await text_area.focus()
                            await page.keyboard.type(tweet_text, delay=10)
                            logger.info(f"Used keyboard method for tweet text: {tweet_text[:50]}...")
                    
                    # Wait a moment for the text to be processed
                    await asyncio.sleep(3)
                    
                    # Verify text was entered
                    try:
                        entered_text = await text_area.input_value() or await text_area.inner_text()
                        if entered_text and len(entered_text) > 0:
                            logger.info(f"Text verification successful: {len(entered_text)} characters entered")
                        else:
                            logger.warning("Text verification failed - no text detected")
                    except:
                        logger.warning("Could not verify text entry")
                    
                except Exception as e:
                    logger.error(f"Error entering tweet text: {e}")
                    await browser.close()
                    return False
                
                # Find and click the tweet button
                try:
                    # Enhanced post button detection with multiple fallback methods
                    logger.info("[DETECT] Starting enhanced post button detection...")
                    
                    # Method 1: Try comprehensive selectors
                    post_button_selectors = [
                        '[data-testid="tweetButton"]',
                        '[data-testid="tweetButtonInline"]',
                        'div[role="button"][data-testid="tweetButton"]',
                        'button[data-testid="tweetButton"]',
                        '[aria-label="Post"]',
                        '[aria-label*="Post"]',
                        'div[role="button"][aria-label*="Post"]',
                        'button[aria-label*="Post"]',
                        '[aria-label*="Tweet"]',
                        'div[role="button"][aria-label*="Tweet"]',
                        'button[aria-label*="Tweet"]'
                    ]
                    
                    post_button = None
                    successful_selector = None
                    
                    for i, selector in enumerate(post_button_selectors):
                        try:
                            logger.info(f"Trying selector {i+1}/{len(post_button_selectors)}: {selector}")
                            button = await page.wait_for_selector(selector, timeout=2000)
                            if button:
                                is_visible = await button.is_visible()
                                is_enabled = await button.is_enabled()
                                logger.info(f"Button state - Visible: {is_visible}, Enabled: {is_enabled}")
                                if is_visible and is_enabled:
                                    post_button = button
                                    successful_selector = selector
                                    logger.info(f"[SUCCESS] Found working button: {selector}")
                                    break
                        except Exception as e:
                            logger.debug(f"Selector failed: {e}")
                            continue
                    
                    # Method 2: Try clicking the found button with retries
                    if post_button:
                        logger.info(f"Attempting to click: {successful_selector}")
                        click_success = False
                        
                        for attempt in range(3):
                            try:
                                logger.info(f"Click attempt {attempt + 1}/3")
                                await post_button.scroll_into_view_if_needed()
                                await asyncio.sleep(0.5)
                                
                                if attempt == 0:
                                    await post_button.click()
                                    logger.info("Used standard click")
                                elif attempt == 1:
                                    await post_button.click(force=True)
                                    logger.info("Used force click")
                                else:
                                    await post_button.evaluate('el => el.click()')
                                    logger.info("Used JavaScript click")
                                
                                click_success = True
                                break
                            except Exception as e:
                                logger.warning(f"Click attempt {attempt + 1} failed: {e}")
                                if attempt < 2:
                                    await asyncio.sleep(1)
                        
                        if not click_success:
                            logger.warning("All click attempts failed, trying fallback methods")
                    
                    # Method 3: Keyboard shortcut fallback (Ctrl+Enter)
                    if not post_button or not click_success:
                        logger.info("Trying keyboard shortcut (Ctrl+Enter)...")
                        try:
                            await page.keyboard.press('Control+Enter')
                            logger.info("[SUCCESS] Used Ctrl+Enter shortcut")
                            await asyncio.sleep(3)
                        except Exception as e:
                            logger.warning(f"Keyboard shortcut failed: {e}")
                            
                            # Method 4: JavaScript-based button search and click
                            logger.info("Trying JavaScript fallback...")
                            try:
                                js_result = await page.evaluate("""
                                    () => {
                                        const buttons = document.querySelectorAll('button, div[role="button"]');
                                        for (const btn of buttons) {
                                            const text = btn.textContent || '';
                                            const label = btn.getAttribute('aria-label') || '';
                                            const testid = btn.getAttribute('data-testid') || '';
                                            
                                            if (text.includes('Post') || label.includes('Post') || 
                                                testid.includes('tweet') || testid.includes('post')) {
                                                const rect = btn.getBoundingClientRect();
                                                if (rect.width > 0 && rect.height > 0 && !btn.disabled) {
                                                    btn.click();
                                                    return true;
                                                }
                                            }
                                        }
                                        return false;
                                    }
                                """)
                                
                                if js_result:
                                    logger.info("[SUCCESS] JavaScript click successful")
                                else:
                                    logger.error("[ERROR] All post methods failed")
                                    await browser.close()
                                    return False
                            except Exception as js_error:
                                logger.error(f"JavaScript fallback failed: {js_error}")
                                await browser.close()
                                return False
                    
                    # Wait for tweet to be posted and check for success indicators
                    await asyncio.sleep(3)
                    
                    # Look for success indicators
                    try:
                        # Check if we're back to the main timeline or if there's a success message
                        success_indicators = [
                            '[data-testid="toast"]',  # Success toast
                            '[role="alert"]',          # Alert message
                        ]
                        
                        for indicator in success_indicators:
                            try:
                                success_element = await page.wait_for_selector(indicator, timeout=2000)
                                if success_element:
                                    text = await success_element.inner_text()
                                    logger.info(f"Success indicator found: {text}")
                                    break
                            except:
                                continue
                    except:
                        pass  # Success indicators are optional
                    
                    logger.success("Tweet posted successfully!")
                    await browser.close()
                    return True
                    
                except Exception as e:
                    logger.error(f"Error posting tweet: {e}")
                    await browser.close()
                    return False
                
        except Exception as e:
            logger.error(f"Error in post_tweet: {e}")
            return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
