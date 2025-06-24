# Crypto Market Sentiment Analysis

## Goal
To predict short-term price movement of selected cryptocurrencies (1-hour window) using real-time Twitter sentiment and market data.

## Data Sources
- Twitter (scraped using Selenium)
- Bitfinex API (for live crypto prices)

## Progress So Far
- Selenium scraper built and tested
- Bitfinex API integration started
- Working on sentiment tagging and regression modeling

## Files in Repo
- `twitter_scraper.py`: Extracts tweets from Twitter's 'Latest' tab using headless browser
- [To be added]: API scripts, sentiment scoring, regression notebook

## Timeline
Project is being developed incrementally; targeting first end-to-end MVP in ~1 week.

## Next Steps
- Collect sufficient data
- Preprocess and clean tweet texts
- Apply regression to predict 1-hour price shift
