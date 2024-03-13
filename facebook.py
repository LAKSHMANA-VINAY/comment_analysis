from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from textblob import TextBlob
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def sentimental_analysis(sentence):
        analysis = TextBlob(sentence)
        if analysis.sentiment.polarity < 0:
            return True
        else:
            False

def fetch_latest_facebook_post(username):
    global facebook_caption
    url = f"https://www.facebook.com/{username}"
    print(url)
    service = Service('../chromedriver-win64/chromedriver.exe')
    service.start()
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    driver.maximize_window()
    time.sleep(2) 
    try:
        close_button = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[1]/div/div[2]/div/div/div/div[1]/div'))
        )
        actions = ActionChains(driver)
        actions.move_to_element(close_button).perform()
        driver.execute_script("arguments[0].click();", close_button)
        comments_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[2]/div/div/div[4]/div/div/div[2]/div[2]/div/div[2]/span/span'))
        )
        time.sleep(5)
        facebook_caption=driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[2]/div/div/div[3]/div[1]/div/div/div/span/div[1]/div")
        facebook_caption=facebook_caption.text
        actions.move_to_element(comments_button).perform()
        driver.execute_script("arguments[0].click();", comments_button)
        time.sleep(5) 
        comment_elements = driver.find_elements(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div/div[2]/div[3]/div/div/div/div/div[1]/div[2]/div[1]/div[1]/div/div/div/div/div/span") 
        print(comment_elements[0].text)
        for comment in comment_elements:
            if sentimental_analysis(comment.text):
                 print(f'{facebook_caption}: {comment.text}')
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        return True
def main():
     username=input("Enter Facebook Username: ")
     fetch_latest_facebook_post(username)

if __name__=='__main__':
     main()
