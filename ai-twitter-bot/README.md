
# AI Twitter Bot 🤖


A smart Twitter bot that automatically posts interesting AI and tech news every day. It finds the latest articles, creates engaging tweets, and posts them to your Twitter account.


## What It Does






- 📰 **Finds News**: Gets the latest AI and tech articles from news websites
- 🧠 **Creates Tweets**: Uses AI to write engaging tweets about the articles
- 🐦 **Posts Automatically**: Shares tweets on your Twitter account without manual work
- ⏰ **Smart Timing**: Posts at different times each day to look natural
- 🔒 **Safe & Secure**: Works without needing Twitter's official API


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








1. **Finds Articles**: Searches news websites for the latest AI and tech stories
2. **Creates Tweets**: 
   - First AI (Groq) writes a draft tweet
   - Second AI (Ollama) makes it sound more natural and engaging
3. **Checks Quality**: Makes sure the tweet is good enough and not too long
4. **Posts Tweet**: Shares it on your Twitter account
5. **Waits**: Automatically waits until the next day to post again


## Settings You Can Change






- **RSS_FEED_URL**: Which news website to follow
- **POST_TIME_HOUR/MINUTE**: What time to post each day
- **RANDOM_DELAY_MINUTES**: How much to vary the posting time
- **MAX_TWEET_LENGTH**: Maximum characters per tweet (default: 270)
- **MIN_ENGAGEMENT_SCORE**: How engaging tweets need to be


## Changing News Sources


**How Hard: Very Easy** 🟢


To follow different news websites:




1. **Update Settings**: Change `RSS_FEED_URL` in your `.env` file
2. **Test It**: Run `python src/rss_aggregator.py` to make sure it works
3. **Small Adjustments**: You might need minor tweaks for different websites





Works with:
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