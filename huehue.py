
# Import Dependencies
import selenium
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from time import sleep
import os
from unidecode import unidecode
import sys
from datetime import datetime
from fake_headers import Headers
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
#from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager


#PATH = os.path.join("C:", "Users", "Payal Dutta", ".wdm", "drivers", "chromedriver", "win64", "137.0.7151.68", "chromedriver-win32", "chromedriver.exe")
PATH = r"C:\Users\Payal Dutta\.wdm\drivers\chromedriver\win64\137.0.7151.68\chromedriver-win32\chromedriver.exe"
follower_threshold = 1000
service = Service(executable_path=PATH)
header = Headers().generate()["User-Agent"]
browser_option = ChromeOptions()
browser_option.add_argument("--no-sandbox")
browser_option.add_argument("--disable-dev-shm-usage")
browser_option.add_argument("--ignore-certificate-errors")
browser_option.add_argument("--disable-gpu")
browser_option.add_argument("--log-level=3")
browser_option.add_argument("--disable-notifications")
browser_option.add_argument("--disable-popup-blocking")
browser_option.add_argument("--user-agent={}".format(header))

driver = webdriver.Chrome(service=service, options=browser_option,)
#driver = _get_driver()
driver.get("https://x.com/i/flow/login")

subject = 'Bitcoin'
sleep(3)

# Setup the log in
your_username = os.environ["twitter_username"]
your_password = os.environ["twitter_password"]
username = driver.find_element(By.XPATH, "//input[@autocomplete='username']")
username.send_keys(your_username)
next_button = driver.find_element(By.XPATH,"//span[contains(text(),'Next')]")
next_button.click()

sleep(3)
try:
    password = driver.find_element(By.XPATH,"//input[@name='password']")
except:
    your_email = os.environ['email']
    put_email = driver.find_element(By.XPATH,"//input[@name='text']")
    put_email.send_keys(your_email)
    next_button = driver.find_element(By.XPATH,"//span[contains(text(),'Next')]")
    next_button.click()
    sleep(2)
    password = driver.find_element(By.XPATH,"//input[@name='password']")
    
password.send_keys(your_password)
log_in = driver.find_element(By.XPATH,"//span[contains(text(),'Log in')]")
log_in.click()

# Search item and fetch it
sleep(3)

search = driver.get(f"https://x.com/search?q={subject}&src=typed_query&f=live")
sleep(3)
#latest = driver.find_element(By.XPATH,"//span[contains(text(),'Latest')]")
#latest.click()

sleep(3)

tweet_links=[]
UserTags=[]
follower_counts = []
TimeStamps=[]
Tweets=[]
Replys=[]
reTweets=[]
Likes=[]
scroll_count = 0
actions = ActionChains(driver)
while True:
    articles = driver.find_elements(By.XPATH,"//article[@data-testid='tweet']")
    for article in articles:
        try:
            TimeStamp = article.find_element(By.XPATH,".//time").get_attribute('datetime')
        except:
            TimeStamp = "no timestamp, might be an ad"
            continue   
        try: 
            Tweet = article.find_element(By.XPATH,".//div[@data-testid='tweetText']").text
        except NoSuchElementException:
            continue        # Might be an image tweet
        try:
            UserTag = article.find_element(By.XPATH,".//span[contains(text(),'@')]")
        except NoSuchElementException:
            continue
        try:
            actions.move_to_element(UserTag).perform()
            sleep(1)
            hover_card = driver.find_element(By.XPATH,"//div[@data-testid='hoverCardParent']")
            follower_count = driver.find_element(By.XPATH, '(//a[contains(@href, "verified_followers")]/span)[1]').text
            follower_count = follower_count.replace(',', '').upper()
            if 'K' in follower_count:
                follower_count = int(float(follower_count.replace('K', '')) * 1000)
            elif 'M' in follower_count:
                follower_count = int(float(follower_count.replace('M', '')) * 1000000)  
            else:
                follower_count = int(re.sub(r'\D', '', follower_count))  # Remove non-numeric characters
            if int(follower_count) < follower_threshold:                     
                continue
        except:
            print("Hover card not found or no followers")
            continue
        tweet_link = article.find_element(By.XPATH, "//a[contains(@href, '/status/')]").get_attribute("href")
        if tweet_link not in tweet_links:
            #Tweets.append(unidecode(Tweet))
            tweet_links.append(tweet_link)
            Tweets.append(Tweet)
            follower_counts.append(follower_count)
            TimeStamps.append(TimeStamp)    
            UserTags.append(UserTag.text)
            
            
            Reply = article.find_element(By.XPATH,".//button[@data-testid='reply']").text
            Replys.append(Reply)
            
            reTweet = article.find_element(By.XPATH,".//button[@data-testid='retweet']").text
            reTweets.append(reTweet)
            
            Like = article.find_element(By.XPATH,".//button[@data-testid='like']").text
            Likes.append(Like)
    if scroll_count > 2:
        profile_button = driver.find_element(By.XPATH,"//button[@aria-label='Account menu']")
        profile_button.click()
        sleep(2)
        logout = driver.find_element(By.XPATH,"//span[contains(text(),'Log out')]")
        logout.click()
        sleep(3)
        break
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
    sleep(3)
    #articles = driver.find_elements(By.XPATH,"//article[@data-testid='tweet']")
    scroll_count += 1
driver.quit()

print(len(UserTags),
len(TimeStamps),
len(Tweets),
len(Replys),
len(reTweets),
len(Likes))




df = pd.DataFrame(zip(UserTags,follower_counts,TimeStamps,Tweets,Replys,reTweets,Likes)
                  ,columns=['UserTags','follower_counts','TimeStamps','Tweets','Replys','reTweets','Likes'])

#df.to_excel(r"C:\crypto_project\tweets_live.xlsx",index=False)
#os.system('start "excel" "C:\crypto_project\tweets_live.xlsx"')

#folder_path = os.path.join("C:", "crypto_project", "tweets")
folder_path = r"C:\crypto_project\tweets"
if not os.path.exists(folder_path):
    os.makedirs("C:\\crypto_project\\tweets", exist_ok=True)
now = datetime.now()
current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
file_path = os.path.join(folder_path, f"{current_time}_tweets_1-{len(UserTags)}.csv")
#file_path = f"{folder_path}{current_time}_tweets_1-{len(UserTags)}.csv"
pd.set_option("display.max_colwidth", None)
df.to_csv(file_path, index=False, encoding="utf-8-sig")

print("CSV Saved: {}".format(file_path))
