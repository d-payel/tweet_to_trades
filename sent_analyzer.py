from transformers import TextClassificationPipeline, AutoModelForSequenceClassification, AutoTokenizer
import pandas as pd

df = pd.read_excel(r"C:\Users\Payal Dutta\Downloads\2025-06-12_20-28-07_tweets_1-34.xlsx")
#print(df['Tweets'].head())

model_name = "ElKulako/cryptobert"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
pipe = TextClassificationPipeline(model=model, tokenizer=tokenizer, max_length=64, truncation=True, padding = 'max_length')
'''
post_1 & post_3 = bullish, post_2 = bearish
post_1 = " see y'all tomorrow and can't wait to see ada in the morning, i wonder what price it is going to be at. 😎🐂🤠💯😴, bitcoin is looking good go for it and flash by that 45k. "
post_2 = "  alright racers, it’s a race to the bottom! good luck today and remember there are no losers (minus those who invested in currency nobody really uses) take your marks... are you ready? go!!" 
post_3 = " i'm never selling. the whole market can bottom out. i'll continue to hold this dumpster fire until the day i die if i need to." 
df_posts = [post_1, post_2, post_3]
'''
preds = pipe(df['Tweets'].head().tolist())
print(preds)
