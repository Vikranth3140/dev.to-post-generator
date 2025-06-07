# Automating Twitter Sentiment Analysis with Python and Tweepy

In this step-by-step guide, we'll walk through setting up an automation for real-time Twitter sentiment analysis using Python and the `Tweepy` library. This project is perfect for data analysts, developers, and anyone interested in social media analytics or natural language processing (NLP).

## Setting Up Your Environment

1. Install required libraries:
```bash
pip install tweepy nltk textblob matplotlib pandas
```

2. Set up your Twitter API credentials: [Twitter Developer Account](https://developer.twitter.com/)

## Connecting to the Twitter API with Tweepy

3. Create a new Python script and import necessary libraries:

```python
import tweepy
from textblob import TextBlob
import matplotlib.pyplot as plt

# Set up your Twitter API credentials here
consumer_key = 'YOUR_CONSUMER_KEY'
consumer_secret = 'YOUR_CONSUMER_SECRET'
access_token = 'YOUR_ACCESS_TOKEN'
access_token_secret = 'YOUR_ACCESS_TOKEN_SECRET'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
```

4. Create a function to analyze the sentiment of a given tweet:

```python
def analyze_tweet_sentiment(tweet):
    analysis = TextBlob(tweet)
    polarity = analysis.polarity
    subjectivity = analysis.subjectivity
    return {'polarity': polarity, 'subjectivity': subjectivity}
```

## Analyzing Sentiments in Real-Time

5. Create a function to fetch and analyze tweets:

```python
def fetch_tweets_and_analyze_sentiment(keyword):
    for tweet in api.search(q=keyword, count=100, lang='en'):
        print(tweet.text)
        sentiment = analyze_tweet_sentiment(tweet.text)
        print(f'Polarity: {sentiment["polarity"]}, Subjectivity: {sentiment["subjectivity"]}')
```

6. Run the script to analyze tweets containing a specific keyword:

```python
fetch_tweets_and_analyze_sentiment('bitcoin')
```

## Automating Your Sentiment Analysis with Stream

7. Modify your script to fetch and analyze tweets continuously using Tweepy's `StreamListener`:

```python
class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        print(status.text)
        sentiment = analyze_tweet_sentiment(status.text)
        print(f'Polarity: {sentiment["polarity"]}, Subjectivity: {sentiment["subjectivity"]}')

    def on_error(self, status_code):
        if status_code == 420:
            return False

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
myStream.filter(track=['bitcoin'], is_async=True, lang='en')
```

8. Run the updated script to start fetching and analyzing tweets in real-time.

## Wrapping Up

With this project, you now have a continuous Twitter sentiment analysis automation using Python and Tweepy. This setup can be easily customized to analyze different keywords or even multiple keywords simultaneously. Explore further by adding data visualization, such as line graphs for polarity over time, to gain insights into trends and sentiments surrounding specific topics on Twitter.