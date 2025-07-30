import pandas as pd
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
import time

def detect_language(text):
    
    try:
        # The detect function can be unreliable for very short/noisy text.
        # We only return a language if the text is long enough.
        if isinstance(text, str) and len(text.strip()) > 10:
            return detect(text)
        else:
            return 'unknown' # Treat short/empty tweets as unknown
    except LangDetectException:
        # This exception is thrown if the language cannot be determined
        return 'unknown'

def translate_to_english(text, source_lang):
    """
    Translates text to English if it's not already English.
    """
    # We don't need to translate English or unknown/short text
    if source_lang in ['en', 'unknown']:
        return text
    
    try:
        # Use a small delay to be respectful of the translation API
        time.sleep(0.5) 
        translated_text = GoogleTranslator(source=source_lang, target='en').translate(text)
        return translated_text
    except Exception as e:
        print(f"Could not translate text from '{source_lang}': {text}. Error: {e}")
        return text # Return the original text if translation fails

def process_tweets_for_language(df):
    """
    Main function to add language detection and translation columns to a DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing a 'Tweets' column.
        
    Returns:
        pd.DataFrame: The DataFrame with new 'language' and 'tweet_english' columns.
    """
    print("Starting language detection...")
    # 1. Detect the language of each tweet
    df['language'] = df['Tweets'].apply(detect_language)
    print("Language detection complete.")
    
    # Report the language distribution
    language_counts = df['language'].value_counts()
    print("\nLanguage distribution found:")
    print(language_counts)
    
    print("\nStarting translation of non-English tweets...")
    # 2. Translate non-English tweets
    # We apply the function row-wise to pass both the text and its detected language
    df['tweet_english'] = df.apply(
        lambda row: translate_to_english(row['Tweets'], row['language']),
        axis=1
    )
    print("Translation complete.")
    
    return df
