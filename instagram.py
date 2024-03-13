from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import instaloader
import time

def fetch_latest_instagram_post(username):
    url = "https://www.instagram.com/p/"
    L = instaloader.Instaloader()
    myusername='username' #my username
    password='password' #my password
    L.context.log("Logging in...")
    L.login(myusername, password)    
    profile = instaloader.Profile.from_username(L.context, username)
    for post in profile.get_posts():
        latest_post = post
        break 
    url += latest_post.shortcode

    return url

def fetch_latest_instagram_post_comments(instagram_post_url):
    print(instagram_post_url)
    service = Service('./chromedriver-win64/chromedriver.exe')
    service.start()
    driver = webdriver.Chrome(service=service)
    driver.get(instagram_post_url)
    time.sleep(15) 
    comment_elements = driver.find_elements(By.XPATH, '/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/div[1]/div/article/div/div[2]/div/div[2]/div[1]/ul/div/div/div/div/ul/div/li/div/div/div[2]/div[1]/span')
    print("Comments:")
    for comment in comment_elements:
        print(comment.text)
    driver.quit()

def main():
    public_username_instagram = input("Enter Instagram Username: ")
    instagram_post_url = fetch_latest_instagram_post(public_username_instagram)
    fetch_latest_instagram_post_comments(instagram_post_url)
    
if __name__ == '__main__':
    main()
