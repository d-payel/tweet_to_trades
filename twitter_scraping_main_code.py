# Import Dependencies
import selenium
from selenium_stealth import stealth
import re
import random
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from time import sleep, time, strftime
import os
from unidecode import unidecode
import sys
from datetime import datetime, timedelta
from fake_headers import Headers
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException  
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import threading
import keyboard

#import sent_analyzer as st_analyzer
script_dir = os.path.dirname(os.path.realpath(__file__))
dotenv_path = os.path.join(script_dir, 'secrets', '.env')
load_dotenv(dotenv_path=dotenv_path)


class scraping:
    def __init__(self, subject, follower_threshold, interval, folder_path) -> None :
        self.subject = subject
        self.follower_threshold = follower_threshold
        self.interval = interval
        self.folder_path = folder_path

    def setup_driver(self):

        header = Headers().generate()["User-Agent"]
        browser_option = ChromeOptions()
        browser_option.add_argument("--no-sandbox")
        browser_option.add_argument("--disable-dev-shm-usage")
        browser_option.add_argument("--ignore-certificate-errors")
        browser_option.add_argument("--disable-gpu")
        browser_option.add_argument("--log-level=3")
        browser_option.add_argument("--disable-notifications")
        browser_option.add_argument("--disable-popup-blocking")
        browser_option.add_argument("--headless")  # Uncomment if you want headless mode
        browser_option.add_argument(f"--user-agent={header}")

        # --- STEALTH OPTIONS ---
        browser_option.add_experimental_option("excludeSwitches", ["enable-automation"])
        browser_option.add_experimental_option('useAutomationExtension', False)
        # --- END NEW ---

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=browser_option)
        
        # --- APPLY STEALTH ---
        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        # --- END STEALTH ---

        return self.driver
    
    def login_(self):
        
        self.driver.get("https://x.com/i/flow/login")
        WebDriverWait(self.driver, 10).until(
            lambda d: d.find_elements(By.XPATH, "//input[@autocomplete='username']")
        )
        your_username = os.getenv("twitter_username")
        your_password = os.getenv("twitter_password")
        username = self.driver.find_element(By.XPATH, "//input[@autocomplete='username']")
        username.send_keys(your_username)
        next_button = self.driver.find_element(By.XPATH,"//span[contains(text(),'Next')]")
        next_button.click()
        try:
            WebDriverWait(self.driver, 10).until(lambda d: d.find_elements(By.XPATH, "//input[@name='password']"))
            password = self.driver.find_element(By.XPATH,"//input[@name='password']")
        except TimeoutException: # Use specific exception
            your_email = os.environ['email']
            put_email = self.driver.find_element(By.XPATH,"//input[@name='text']")
            put_email.send_keys(your_email)
            next_button = self.driver.find_element(By.XPATH,"//span[contains(text(),'Next')]")
            next_button.click()
            WebDriverWait(self.driver, 10).until(lambda d: d.find_elements(By.XPATH, "//input[@name='password']"))
            password = self.driver.find_element(By.XPATH,"//input[@name='password']")
        password.send_keys(your_password)
        log_in = self.driver.find_element(By.XPATH,"//span[contains(text(),'Log in')]")
        log_in.click()
        try:
            WebDriverWait(self.driver, 10).until(lambda d: d.current_url.startswith("https://x.com/home") or d.find_elements(By.XPATH, "//a[@aria-label='Home']"))
            print("Logged in successfully.")
        except Exception:
            print("Login failed.")
            self.driver.quit()
            sys.exit(1)
        return self.driver
    
    def logout_session(self):
        
        if not hasattr(self, 'driver') or not self.driver.service.is_connectable():
            print("Driver not initialized or already closed.")
            return
        try:
            self.driver.get("https://x.com/logout")
            WebDriverWait(self.driver, 10).until(lambda d: d.find_elements(By.XPATH, "//span[contains(text(),'Log out')]"))
            logout = self.driver.find_elements(By.XPATH,"//span[contains(text(),'Log out')]")
            logout[1].click()
            WebDriverWait(self.driver, 10).until(lambda d: d.find_elements(By.XPATH, "//a[@href='/login']"))
            print("Logged out successfully.")
        except Exception as e:
            print(f"Logout failed: {e}")
        
        finally:
            self.driver.quit()
            print("Driver closed successfully.")
        
        return
    
    def stage_one_scraper(self):
        
        try:
            self.driver.get(f"https://x.com/search?q={self.subject}&src=typed_query&f=live")
            WebDriverWait(self.driver, 15).until(lambda d: d.find_elements(By.XPATH, "//article[@data-testid='tweet']"))
            print("Successfully navigated to the search page.")
        except Exception as e:
            print(f"Error navigating to search page: {e}")
            return None

        tweet_ids, UserTags, follower_counts, TimeStamps, Tweets = [], [], [], [], []
        actions = ActionChains(self.driver)
        start_time = datetime.now()
        
        # Variables for smart scrolling
        last_position = self.driver.execute_script("return window.pageYOffset;")
        stuck_counter = 0

        while datetime.now() < start_time + timedelta(minutes=self.interval):
            
            # Error Handling: Check for "Retry" button
            try:
                if self.driver.find_element(By.XPATH, "//span[text()='Retry']"):
                    print("Detected 'Something went wrong'. Pausing and refreshing.")
                    sleep(30)
                    self.driver.refresh()
                    sleep(5)
                    continue
            except NoSuchElementException:
                pass

            articles = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
            
            new_tweets_found_in_pass = False
            for article in articles:
                try:
                    tweet_link_element = article.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
                    tweet_id = tweet_link_element.get_attribute("href").split('/')[-1]

                    if tweet_id in tweet_ids:
                        continue

                    new_tweets_found_in_pass = True

                    #TimeStamp = article.find_element(By.XPATH, ".//time").get_attribute('datetime')
                    Tweet = article.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
                    UserTag = article.find_element(By.XPATH, ".//span[contains(text(),'@')]")

                    actions.move_to_element(UserTag).perform()
                    sleep(random.uniform(0.8, 1.3))
                    
                    follower_count_raw = self.driver.find_element(By.XPATH, '(//a[contains(@href, "verified_followers")]/span)[1]').text
                    follower_count_str = follower_count_raw.replace(',', '').upper()
                    
                    if 'K' in follower_count_str: follower_count = int(float(follower_count_str.replace('K', '')) * 1000)
                    elif 'M' in follower_count_str: follower_count = int(float(follower_count_str.replace('M', '')) * 1000000)
                    else: follower_count = int(re.sub(r'\D', '', follower_count_str))

                    if follower_count >= self.follower_threshold:
                        print(f"Found valid tweet from {UserTag.text} ({follower_count} followers).")
                        tweet_ids.append(tweet_id)
                        Tweets.append(" ".join(Tweet.split()))
                        follower_counts.append(follower_count)
                        TimeStamps.append(TimeStamp)
                        UserTags.append(UserTag.text)

                except Exception:
                    continue

            # --- Smart Scrolling Logic ---
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(random.uniform(2.0, 3.5))
            
            current_position = self.driver.execute_script("return window.pageYOffset;")
            if last_position == current_position and not new_tweets_found_in_pass:
                stuck_counter += 1
                print(f"Scroll position hasn't changed. Stuck counter: {stuck_counter}")
                if stuck_counter > 4:
                    print("Feed appears to have ended. Breaking loop.")
                    break
            else:
                stuck_counter = 0
            last_position = current_position

            # --- Stochastic Human Interaction Logic ---
            # 3% chance to perform an interaction to appear more human
            if random.random() < 0.03: 
                try:
                    print("--- Performing humanizing interaction ---")
                    all_visible_tweets = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
                    if all_visible_tweets:
                        random_tweet_to_interact = random.choice(all_visible_tweets)
                        
                        # 70% chance to Like, 30% chance to Retweet
                        if random.random() < 0.7:
                            like_button = random_tweet_to_interact.find_element(By.XPATH, ".//button[@data-testid='like']")
                            self.driver.execute_script("arguments[0].click();", like_button) # More robust click
                            print("Action: Liked a random tweet.")
                        else:
                            retweet_button = random_tweet_to_interact.find_element(By.XPATH, ".//button[@data-testid='retweet']")
                            self.driver.execute_script("arguments[0].click();", retweet_button)
                            sleep(1)
                            confirm_retweet = self.driver.find_element(By.XPATH, "//div[@data-testid='retweetConfirm']")
                            self.driver.execute_script("arguments[0].click();", confirm_retweet)
                            print("Action: Retweeted a random tweet.")
                        
                        sleep(random.uniform(4, 8)) # Pause longer after an interaction
                except Exception as e:
                    print(f"Could not perform interaction: {e}")

        # --- DataFrame Creation and Saving ---
        if not UserTags:
            print("No tweets found meeting the criteria in the given interval.")
            return None

        df = pd.DataFrame(zip(UserTags, follower_counts, TimeStamps Tweets, tweet_ids),
                        columns=['UserTags', 'follower_counts', 'TimeStamps', 'Tweets', 'tweet_ids'])
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(self.folder_path, f"{current_time}_tweets_{len(UserTags)}.csv")
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"CSV Saved: {file_path} with {len(df)} tweets.")
        
        return file_path    
    def stage_two_scraper(self, file_path_to_revisit): # Accept file path as argument
        print("In stage two scraper...")
        if file_path_to_revisit is None:
            print("No file path provided from Stage 1. Skipping Stage 2.")
            return None
            
        df = pd.read_csv(file_path_to_revisit) # Use the argument
        tweet_ids, usertags = df['tweet_ids'].tolist(), df['UserTags'].tolist()
        retweets, delayedTimeStamps = [], []
        
        if not hasattr(self, 'driver'):
            print("Driver not initialized. Please run login_() first.")
            return None

        for usertag, tweet_id in zip(usertags, tweet_ids):
            try:
                usertag_clean = usertag.replace('@', '')
                tweet_link = f"https://x.com/{usertag_clean}/status/{tweet_id}"
                self.driver.get(tweet_link)
                WebDriverWait(self.driver, 10).until(lambda d: d.find_elements(By.XPATH, "//article[@data-testid='tweet']"))
                
                retweet_raw = self.driver.find_element(By.XPATH, ".//button[@data-testid='retweet']").text
                retweet = retweet_raw.replace(',', '').upper()
                if retweet == '': 
                    retweet = '0'
                retweets.append(retweet)
                delayedTimeStamps.append(self.driver.find_element(By.XPATH,".//time").get_attribute('datetime'))
            except Exception as e:
                print(f"Could not process tweet {tweet_id}. Error: {e}")
                retweets.append('ERROR')
                delayedTimeStamps.append('ERROR')
                continue
                
        df['retweets'] = retweets
        df['creationTimeStamps_UTC'] = delayedTimeStamps
        print("Retweet count and creation timestamps added to the DataFrame.")

        updated_file_path = file_path_to_revisit.replace('.csv', '_updated.csv') 
        df.to_csv(updated_file_path, index=False, encoding="utf-8-sig")
        print(f"Updated csv Saved: {updated_file_path}")
        return updated_file_path

# ============================
# Main Execution Logic
# ============================
'''
if __name__ == "__main__":
    subject = "Bitcoin"
    follower_threshold = 1000
    scrape_interval_minutes = 10
    revisit_wait_seconds = 900
    total_cycle_duration_seconds = 1800
    
    folder_path = r"C:\crypto_project\tweets"
    os.makedirs(folder_path, exist_ok=True)

    scraper_instance = scraping(subject, follower_threshold, scrape_interval_minutes, folder_path)
    scraper_instance.setup_driver()
    scraper_instance.login_()
    sleep(2)
    scraper_instance.logout_session()
    sleep(20)
'''
# THE MAIN THING

stop_flag = threading.Event()

def listen_for_stop_key():
    print("\n>>> The scraper is running. Press the 'ESC' key at any time to stop gracefully. <<<")
    keyboard.wait('esc')
    print("\n>>> Stop signal received! Finishing the current cycle before exiting... <<<")
    stop_flag.set()

if __name__ == "__main__":
    subject = "Bitcoin"
    follower_threshold = 750
    scrape_interval_minutes = 2
    revisit_wait_seconds = 600
    total_cycle_duration_seconds = 900
    
    folder_path = r"C:\crypto_project\tweets"
    os.makedirs(folder_path, exist_ok=True)

    scraper_instance = scraping(subject, follower_threshold, scrape_interval_minutes, folder_path)
    scraper_instance.setup_driver()
    scraper_instance.login_()

    listener_thread = threading.Thread(target=listen_for_stop_key)
    listener_thread.daemon = True
    listener_thread.start()
    
    iteration_count = 1
    while not stop_flag.is_set():
        cycle_start_time = time()
        print(f"\n--- Starting Iteration {iteration_count} at {strftime('%H:%M:%S')} ---")
        
        file_to_revisit = scraper_instance.stage_one_scraper()

        if file_to_revisit:
            print(f"Stage 1 complete. Sleeping for {revisit_wait_seconds / 60:.0f} minutes before revisit...")
            stop_flag.wait(revisit_wait_seconds)
            if stop_flag.is_set(): break

            print("Waking up. Starting Stage 2: Revisiting tweets for engagement...")
            scraper_instance.stage_two_scraper(file_to_revisit)
        else:
            print("Stage 1 did not produce a file, moving to next cycle.")
        
        print(f"Iteration {iteration_count} complete.")
        iteration_count += 1
        
        elapsed_time = time() - cycle_start_time
        sleep_time = total_cycle_duration_seconds - elapsed_time
        if sleep_time > 0:
            print(f"Cycle took {elapsed_time:.0f} seconds. Sleeping for {sleep_time:.0f} seconds...")
            stop_flag.wait(sleep_time)
        else:
            print(f"Warning: Cycle took {elapsed_time:.0f}s, longer than target {total_cycle_duration_seconds}s.")

    print("\nLoop terminated. Shutting down...")
    scraper_instance.logout_session()
    print("Pipeline finished.")
'''
if __name__ == "__main__":
    subject = "Bitcoin"
    follower_threshold = 500
    scrape_interval_minutes = 10
    revisit_wait_seconds = 900
    total_cycle_duration_seconds = 1800
    
    folder_path = r"C:\crypto_project\tweets"
    os.makedirs(folder_path, exist_ok=True)

    scraper_instance = scraping(subject, follower_threshold, scrape_interval_minutes, folder_path)
    scraper_instance.setup_driver()
    scraper_instance.login_()   
    scraper_instance.stage_two_scraper(r"C:\crypto_project\tweets\2025-07-22_12-43-23_tweets_77.csv") 
    scraper_instance.logout_session()
    print("Pipeline finished.")
'''
