# AI Twitter Bot

A sophisticated AI-powered Twitter bot that automatically discovers, analyzes, and posts high-engagement AI and tech news. It uses multiple AI models to create compelling tweets from the best articles across 11+ news sources.

## What It Does

- **Finds News**: Gets the latest AI and tech articles from multiple news websites
- **Creates Tweets**: Uses AI to write engaging tweets about the articles
- **Posts Automatically**: Shares tweets on your Twitter account without manual work
- **Smart Timing**: Posts at different times each day to look natural
- **Safe & Secure**: Works without needing Twitter's official API

## Getting Started

### Step 1: Set Up Your Computer
```bash
# Create a new Python environment
python -m venv venvai

venvai\Scripts\activate  # For Windows users

# Install required software
pip install -r requirements.txt

# Install browser automation tools
playwright install chromium
```

### Step 2: Install Ollama (AI Helper)
```bash
# Download Ollama from https://ollama.ai/
# Then run this command:
ollama pull llama3.2:latest
```

### Step 3: Configure Settings
1. Copy the file `.env.example` and rename it to `.env`
2. Add your Groq API key (free from groq.com)
3. Set up when you want tweets to be posted

### Step 4: Connect to Twitter
```bash
# Log into Twitter once to save your session
python src/twitter_poster.py
```

## How to Use

### Post One Tweet Now
```bash
python main.py
```

### Start Daily Automatic Posting
```bash
# This will keep running and post tweets daily
python src/scheduler.py
```

## Project Files

```
AiAgentTweeting_v1/
├── main.py              # Main program
├── config.py            # Settings
├── .env                 # Your personal settings
├── requirements.txt     # Required software list
├── src/
│   ├── rss_aggregator.py    # Finds news articles
│   ├── content_generator.py # Creates tweets
│   ├── twitter_poster.py    # Posts to Twitter
│   └── scheduler.py         # Handles timing
├── twitter_profile/         # Saves your Twitter login
└── logs/                    # Activity records
```

## How It Works

The bot uses a sophisticated AI-powered workflow to create high-quality tweets:

### **Smart Article Selection Process**
1. **Multiple Sources**: Fetches articles from 11+ RSS feeds including MIT Technology Review, OpenAI, Google AI, Hugging Face, and more
2. **Choose 5 Best**: Selects the 5 most promising articles based on engagement scoring
3. **Pick Winner**: Chooses the single best article using AI engagement analysis

### **Intelligent Tweet Creation**
4. **Generate 5 Variations**: Creates 5 different tweet versions using Groq AI
5. **Score Each Tweet**: Analyzes each variation for engagement potential (1-10 scale)
6. **Select Best Tweet**: Picks the highest-scoring tweet variation
7. **Polish Content**: Uses Ollama AI to refine and improve the selected tweet

### **Quality Assurance**
8. **Duplicate Check**: Compares against recent tweets to avoid repetition
9. **Length Validation**: Ensures tweet fits within character limits
10. **Final Review**: Verifies content quality and engagement score

### **Smart Posting**
11. **Post to Twitter**: Automatically shares the tweet with article link
12. **Save History**: Records tweet for future duplicate checking
13. **Schedule Next**: Waits until the next scheduled posting time

## Settings You Can Change

### **Content Settings**
- **RSS_FEED_URLS**: Multiple news sources to follow (11 sources included)
- **MAX_ARTICLES_PER_DAY**: How many articles to fetch (default: 5)
- **MIN_ENGAGEMENT_SCORE**: Minimum engagement score for tweets (1-10 scale)
- **MAX_TWEET_LENGTH**: Maximum characters per tweet (default: 280)

### **Timing Settings**
- **POST_TIME_HOUR/MINUTE**: What time to post each day
- **RANDOM_DELAY_MINUTES**: How much to vary the posting time

### **Quality Control**
- **DUPLICATE_CHECK_DAYS**: How many days back to check for duplicates (default: 3)
- **ENABLE_HASHTAGS**: Whether to add hashtags to tweets
- **MAX_HASHTAGS_PER_TWEET**: Maximum hashtags per tweet (default: 3)

## Changing News Sources

**How Hard: Very Easy**

### **Built-in Sources**
The bot comes with 11 high-quality RSS feeds:
- MIT Technology Review (AI section)
- Reddit Machine Learning & AI communities
- OpenAI News
- Google AI Blog
- Hugging Face Blog
- ArXiv AI papers
- Berkeley AI Research
- VentureBeat AI
- AI News
- Wired AI

### **Adding Custom Sources**
1. **Update Config**: Edit `rss_feed_urls` list in `config.py`
2. **Test Feed**: Run `python src/rss_aggregator.py` to verify it works
3. **Monitor Quality**: Check engagement scores for new sources

### **Source Selection**
The bot automatically:
- Randomly selects from available sources
- Fetches multiple articles per run
- Scores articles for engagement potential
- Chooses the best content for posting

Works with:
- RSS feeds
- Atom feeds
- Most news websites
- Blog feeds
- Tech publication feeds

## Common Problems

- **Can't Login to Twitter**: Delete the `twitter_profile/` folder and login again
- **Ollama Not Working**: Make sure Ollama is running with `ollama serve`
- **Groq API Issues**: Check your API key and usage limits

## Want to Help Improve This?

1. Copy this project to your account
2. Make your improvements
3. Share your changes back

## Legal Stuff

MIT License - You can use this freely

---

**Important**: This is for learning purposes. Make sure you follow Twitter's rules and don't post too frequently.