# Import Dependencies
import selenium
import re
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from time import sleep
import os
from unidecode import unidecode
import sys
from datetime import datetime, timedelta
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



class scraping:
    def __init__(self, subject, follower_threshold, interval, path, folder_path) -> None :
        self.subject = subject      # Name of the coins or subject to be searched
        self.follower_threshold = follower_threshold # Minimum follower count of the user to be considered
        self.interval = interval     # Time interval in minutes for which the scraper will run
        self.path = path        # Path of Chromedriver executable
        self.folder_path = folder_path #Path where the csv files will be saved
        pass

    def setup_driver(self):
        service = Service(executable_path=self.path)
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

        self.driver = webdriver.Chrome(service=service, options=browser_option,)
        return self.driver
    
    def login_(self):
        #driver = self.setup_driver(self.path)
        
        self.driver.get("https://x.com/i/flow/login")
        sleep(3)
        your_username = os.environ["twitter_username"]
        your_password = os.environ["twitter_password"]
        username = self.driver.find_element(By.XPATH, "//input[@autocomplete='username']")
        username.send_keys(your_username)
        next_button = self.driver.find_element(By.XPATH,"//span[contains(text(),'Next')]")
        next_button.click()
        sleep(3)
        try:
            password = self.driver.find_element(By.XPATH,"//input[@name='password']")
        except:
            your_email = os.environ['email']
            put_email = self.driver.find_element(By.XPATH,"//input[@name='text']")
            put_email.send_keys(your_email)
            next_button = self.driver.find_element(By.XPATH,"//span[contains(text(),'Next')]")
            next_button.click()
            sleep(2)
            password = self.driver.find_element(By.XPATH,"//input[@name='password']")
            
        password.send_keys(your_password)
        log_in = self.driver.find_element(By.XPATH,"//span[contains(text(),'Log in')]")
        log_in.click()
        sleep(3)
        return self.driver
    
    def logout_session(self):
        driver=self.driver
        sleep(2)
        profile_button = self.driver.find_element(By.XPATH,"//button[@aria-label='Account menu']")
        profile_button.click()
        sleep(2)
        logout = self.driver.find_element(By.XPATH,"//span[contains(text(),'Log out')]")
        logout.click()
        sleep(3) 
        self.driver.quit()
        return "Logged out successfully and the tab is closed."
    
    def stage_one_scraper(self):         #Scrape the first stage of tweets based on the subject, time interval and follower threshold.
        #driver = self.setup_driver(self.path)
        #driver = self.login_(driver)
        try:
            self.driver.get(f"https://x.com/search?q={self.subject}&src=typed_query&f=live")
            sleep(3)
        except AttributeError as e:
            print("Driver not initialized. Please run the login method first.")
            sys.exit()
            
        tweet_ids=[]
        UserTags=[]
        follower_counts = []
        TimeStamps=[]
        Tweets=[]
        actions = ActionChains(self.driver)
        start_time = datetime.now()

        while datetime.now() < start_time + timedelta(minutes=self.interval):  # Run for a given time window 
            articles = self.driver.find_elements(By.XPATH,"//article[@data-testid='tweet']")
            for article in articles:
                try:
                    TimeStamp = article.find_element(By.XPATH,".//time").get_attribute('datetime')
                except:
                    continue        #no timestamp, might be an ad
                try: 
                    Tweet = article.find_element(By.XPATH,".//div[@data-testid='tweetText']").text
                except NoSuchElementException:
                    continue        # Might be an image tweet
                try:
                    UserTag = article.find_element(By.XPATH,".//span[contains(text(),'@')]")
                except NoSuchElementException:
                    continue
                try:
                    actions.move_to_element(UserTag).perform()          #Hover over the user tag to get the follower count
                    sleep(1)
                    hover_card = self.driver.find_element(By.XPATH,"//div[@data-testid='hoverCardParent']")
                    follower_count = self.driver.find_element(By.XPATH, '(//a[contains(@href, "verified_followers")]/span)[1]').text
                    follower_count = follower_count.replace(',', '').upper()
                    if 'K' in follower_count:
                        follower_count = int(float(follower_count.replace('K', '')) * 1000)
                    elif 'M' in follower_count:
                        follower_count = int(float(follower_count.replace('M', '')) * 1000000)  
                    else:
                        follower_count = int(re.sub(r'\D', '', follower_count))  # Remove non-numeric characters
                    if int(follower_count) < self.follower_threshold:                     
                        continue
                except:
                    print("Hover card not found or no followers")
                    continue
                tweet_link = article.find_element(By.XPATH, "//a[contains(@href, '/status/')]").get_attribute("href")
                tweet_id =  tweet_link.split('/')[-1]  # Extract the tweet ID from the link
                if tweet_id not in tweet_ids:
                    #Tweets.append(unidecode(Tweet))
                    tweet_ids.append(tweet_id)
                    Tweets.append(Tweet)
                    follower_counts.append(follower_count)
                    TimeStamps.append(TimeStamp)    
                    UserTags.append(UserTag.text)
            self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            sleep(3)
    
        #self.logout_session()

        if len(UserTags) == 0:
            print("No tweets found for the given subject and follower threshold.")
            sys.exit()

        df = pd.DataFrame(zip(UserTags,follower_counts,TimeStamps,Tweets,tweet_ids)             # Converting to dataframe
                    ,columns=['UserTags','follower_counts','TimeStamps','Tweets','tweet_ids'])

        folder_path = self.folder_path
        if not os.path.exists(folder_path):                     # Creating the directory if it does not exist
            os.makedirs(folder_path, exist_ok=True)
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(folder_path, f"{current_time}_tweets_1-{len(UserTags)}.csv")       # Save the data to a CSV file
        pd.set_option("display.max_colwidth", None)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print("CSV Saved: {}".format(file_path))
        self.file_path = file_path

        return 

    def stage_two_scraper(self):  # Scrape the retweet count
        
        df = pd.read_csv(self.file_path)
        tweet_ids = df['tweet_ids'].tolist()
        usertags = df['UserTags'].tolist()
        retweets = []
        delayedTimeStamps = []
        if not hasattr(self, 'driver'):
            print("Driver not initialized. Please run login_() first.")
            sys.exit()
        sleep(2)

        for usertag, tweet_id in zip(usertags, tweet_ids):  # Scrape the second stage of tweets based on the tweet links
            try:
                #tweet_link_revisit = driver.find_element(By.XPATH, "//a[contains(@href, f'{tweet_link}')]")
                usertag = usertag.replace('@', '')  # Remove '@' from the user tag
                tweet_link = f"https://x.com/{usertag}/status/{tweet_id}"
                
                self.driver.get(tweet_link)
                sleep(2)
            except NoSuchElementException:
                print(f"Tweet link {tweet_link} not found in the search results.")
                retweets.append('N/A')
                delayedTimeStamps.append('N/A')
                continue
            try:
                retweet =  self.driver.find_element(By.XPATH, ".//button[@data-testid='retweet']").text
                #retweet =  driver.find_element(By.XPATH, "//div[@data-testid='retweet']").text
                delayedTimeStamp = self.driver.find_element(By.XPATH,".//time").get_attribute('datetime')
                retweets.append(retweet)
                delayedTimeStamps.append(delayedTimeStamp)
            except NoSuchElementException:
                print(f"Retweet count not found for tweet ID {tweet_id}.")
                retweets.append('N/A')
                delayedTimeStamps.append('N/A')
                continue
        df['retweets'] = retweets
        df['delayedTimeStamps'] = delayedTimeStamps
        self.logout_session()
        # Save the updated DataFrame to a new XLSX file or overwrite the old one
        updated_file_path = self.file_path.replace('.csv', '_updated.csv')
        df.to_csv(updated_file_path, index=False, encoding="utf-8-sig")
        print(f"Updated csv Saved: {updated_file_path}")
        return updated_file_path
    
    def run_full_pipeline(self):
        self.setup_driver()
        self.login_()
        self.stage_one_scraper()
        print("Sleeping before revisit...")
        sleep(300)  # wait 30 minutes before revisiting
        #self.setup_driver()  # reopen browser
        #self.login_()
        self.stage_two_scraper()


subject = "Bitcoin"
follower_threshold = 1000
interval = 2 # in minutes
PATH = r"C:\Users\Payal Dutta\.wdm\drivers\chromedriver\win64\137.0.7151.68\chromedriver-win32\chromedriver.exe" #Chromedriver path
folder_path = r"C:\crypto_project\tweets" # The directory where the csv files will be saved

first_instance = scraping(subject, follower_threshold, interval, PATH, folder_path)
first_instance.run_full_pipeline()

'''
# For scraping the tweets
first_instance = scraping(subject, follower_threshold, interval, PATH, folder_path)
first_instance.setup_driver()   
first_instance.login_()
first_instance.stage_one_scraper()

# For scraping the retweet count
second_instance = scraping(subject, follower_threshold, interval, PATH, folder_path)
second_instance.setup_driver()      
second_instance.login_()
second_instance.file_path = first_instance.file_path    
second_instance.stage_two_scraper()
'''