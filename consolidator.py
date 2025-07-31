import os
import pandas as pd

# Set the directory where your tweet CSVs are stored
folder_path = r"C:\crypto_project\tweets_1"  # Change this to your folder

# List all CSV files in that directory
csv_files = [file for file in os.listdir(folder_path) if file.endswith('updated.csv')]

# Read and concatenate all into one DataFrame
all_tweets_df = pd.concat(
    [pd.read_csv(os.path.join(folder_path, file)) for file in csv_files],
    ignore_index=True
)

# Drop duplicates based on tweet_id or tweet text
all_tweets_df.drop_duplicates(subset=['tweet_ids'], inplace=True)

# Save the consolidated file
consolidated_path = os.path.join(folder_path, "all_consolidated_tweets.csv")
all_tweets_df.to_csv(consolidated_path, index=False, encoding='utf-8-sig')

print(f"Consolidation complete. File saved at:\n{consolidated_path}")
