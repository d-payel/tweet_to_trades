import pandas as pd
import openpyxl
import requests
from time import sleep
from dotenv import load_dotenv
import os
import sys
try:
    import language_processor as lp
except ImportError:
    print("Error: language_processor.py not found. Make sure it's in the same directory.")
    sys.exit(1)

# --- Load environment variables from .env file ---
script_dir = os.path.dirname(os.path.realpath(__file__)) if __file__ in locals() else os.getcwd()
dotenv_path = os.path.join(script_dir, 'secrets', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Load and Process Tweets ---

df = pd.read_excel(r"C:\crypto_project\tweets_1\consolidated_tweets_June_26`.xlsx", sheet_name="Consolidated_dataset_of_tweets",
                   engine="openpyxl")
print("Data loaded successfully. Processing tweets for language ...")
language_processed_df = lp.process_tweets_for_language(df)
print("Language processing complete. Sample data:")
print(language_processed_df.head())

# --- Configuration ---
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
# IMPORTANT: Paste your Hugging Face API key here
HF_API_KEY = os.getenv("hf_token")
if not HF_API_KEY:
    raise ValueError("Hugging Face API key not found. Please set 'hf_token' in your .env file.")
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# My defined narrative categories
CANDIDATE_LABELS = [
    'Fundamental or Macro News', 
    'Technical Analysis', 
    'Hype and Social Sentiment', 
    'Regulatory or Geopolitical', 
    'FUD or Scam'
]

# --- Function to Query the API ---
def classify_tweet(tweet_text):
    """Sends a tweet to the Hugging Face API for zero-shot classification."""
    payload = {
        "inputs": tweet_text,
        "parameters": {"candidate_labels": CANDIDATE_LABELS}
    }
    response = None
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        result = response.json()
        # The API returns a list of labels and a corresponding list of scores.
        # We find the index of the highest score and get the corresponding label.
        best_label_index = result['scores'].index(max(result['scores']))
        return result['labels'][best_label_index]
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        if response:
            print(f"Response content: {response.text}")
        return "API_ERROR"
    
# --- Main Labeling Logic ---

# Apply the classification function to each tweet
# We add a sleep(1) between each request to respect the API rate limits of the free tier.
print("Starting tweet labelling...")
if 'tweet_english' not in language_processed_df.columns:
    raise ValueError("Column 'tweet_english' not found in the DataFrame. Please check the input data.") 
else:
    language_processed_df['narrative_category'] = language_processed_df['tweet_english'].apply(lambda tweet: (sleep(1), classify_tweet(tweet))[1])
print("Tweet labelling complete. Sample data with labels:")
os.makedirs(r'c:\crypto_project\tweets_1', exist_ok=True)   # To create the directory if it doesn't exist
# Save the labeled DataFrame to a new Excel file    
labeled_file_path = os.path.join(r"c:\crypto_project\tweets_1", 'labeled_tweets_June_26.xlsx')
language_processed_df.to_excel(labeled_file_path, index=False, engine='openpyxl')
# Display the results
print(language_processed_df.head())
