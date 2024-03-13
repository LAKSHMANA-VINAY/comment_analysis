from flask import Flask, render_template, request, redirect, flash,session,jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import asyncio
import instaloader
import time
import mysql.connector
from textblob import TextBlob
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


app = Flask(__name__)
app.secret_key = '@A*Laxman!@$#12!^&77HG'

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'sentimental_analysis'
}

instagram_caption='No Caption'
facebook_caption='No Caption'

connection = mysql.connector.connect(**config)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register')
def register():
    return render_template("register.html")

@app.route("/login",methods=['GET', 'POST'])
def user_login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['pwd']
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT instagram,facebook,twitter FROM users WHERE email = %s and password = %s", (email, password))
            user = cursor.fetchone()

            if user:
                session['email'] = email
                session['instagram']=user[0].strip()
                session['facebook']=user[1].strip()
                session['twitter']=user[2].strip()
                fetch_latest_instagram_post(session['instagram'])
                return redirect('/instagram')
            else:
                return render_template('index.html',msg="Your credentials are Wrong")

        except Exception as e:
            print(e)
            return render_template('index.html',msg="Something went wrong. Please try again")

        finally:
            cursor.close()

@app.route("/user_register", methods=['GET', 'POST'])
def user_register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        instagram = request.form['instagram']
        facebook = request.form['facebook']
        twitter = request.form['twitter']
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user:
                return render_template('register.html',msg="User already exists")

            else:
                cursor.execute("INSERT INTO users (email, password, instagram, facebook, twitter) VALUES (%s, %s, %s, %s, %s)", 
                            (email, password, instagram, facebook, twitter))
                connection.commit()
                return render_template('index.html',msg="Account created successfully")

        except Exception as e:
            return render_template('register.html',msg="Something went wrong. Please try again")

        finally:
            cursor.close()
@app.route('/instagram')
def instagram():
        print("I am in instagram")
        email=session['email']
        type='instagram'
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT caption,comment FROM comments WHERE email = %s and  type= %s", (email, type))
            details = cursor.fetchall()
            comments_list = []
            if details:
                for detail in details:
                    caption = detail[0] 
                    comment = detail[1]  
                    comments_list.append({'caption': caption, 'comment': comment})
                print('-----------------------------------------------------------------------------------------------------')
            return render_template('instagram.html', comments_list=comments_list)
        except Exception as e:
            print(e)
            return render_template('index.html',msg="Something went wrong. Please try again")
        finally:
            cursor.close()

@app.route('/run')
def run():
    result = fetch_latest_instagram_post(session['instagram']) 
    if result:
        return jsonify({'success': True, 'message': 'Function completed successfully.'})
    else:
        return jsonify({'success': False, 'message': 'Function encountered an error.'})

@app.route('/run_facebook')
def run_facebook():
    result = fetch_latest_facebook_post(session['facebook']) 
    if result:
        return jsonify({'success': True, 'message': 'Function completed successfully.'})
    else:
        return jsonify({'success': False, 'message': 'Function encountered an error.'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def sentimental_analysis(sentence):
        analysis = TextBlob(sentence)
        if analysis.sentiment.polarity < 0:
            return True
        else:
            False

def fetch_latest_instagram_post(username):
    global instagram_caption
    url = "https://www.instagram.com/p/"
    L = instaloader.Instaloader()
    myusername='username' #my username
    password='password' #my password
    L.context.log("Logging in...")
    L.login(myusername, password)  
    profile = instaloader.Profile.from_username(L.context, username)
    for post in profile.get_posts():
        latest_post = post
        instagram_caption=post.caption
        if instagram_caption is None:
            instagram_caption='No Caption'
        break 
    url += latest_post.shortcode
    fetch_instagram_comments_with_selenium(url)
    return True

def fetch_instagram_comments_with_selenium(instagram_post_url):
    service = Service('../chromedriver-win64/chromedriver.exe')
    service.start()
    driver = webdriver.Chrome(service=service)
    driver.get(instagram_post_url)
    time.sleep(10) 
    cursor = connection.cursor()
    comment_elements = driver.find_elements(By.XPATH, '/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/div[1]/div/article/div/div[2]/div/div[2]/div[1]/ul/div/div/div/div/ul/div/li/div/div/div[2]/div[1]/span')
    cursor.execute("SELECT caption,comment FROM comments WHERE email = %s and  type= %s ORDER BY id DESC", (session['email'], 'instagram'))
    details = cursor.fetchall()
    if details: 
        for row in details:
            caption = row[0]
            comment = row[1]
            flag=0
            if comment.strip() != comment_elements[0].text.strip():
                for comment in comment_elements:
                    if sentimental_analysis(comment.text):
                        cursor = connection.cursor()
                        cursor.execute("INSERT INTO comments (email, caption, comment, type) VALUES (%s, %s, %s, %s)", 
                                    (session['email'], instagram_caption, comment.text, 'instagram'))
                        connection.commit()
                        cursor.close() 
                        flag=1
                        break
                    else:
                        flag=1
                        break
                if flag==1:
                    break
            else:
                break
    elif not details:
        for comment in reversed(comment_elements):
            if sentimental_analysis(comment.text):
                cursor = connection.cursor()
                cursor.execute("INSERT INTO comments (email, caption, comment, type) VALUES (%s, %s, %s, %s)", 
                            (session['email'], instagram_caption, comment.text, 'instagram'))
                connection.commit()
                cursor.close()
            else:
                continue

    driver.quit()

def fetch_instagram_negative_comments(username):
    global facebook_caption
    url = f"https://www.instagram.com/{username}"
    print(url)
    service = Service('../chromedriver-win64/chromedriver.exe')
    service.start()
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    driver.maximize_window()
    time.sleep(2) 
    click_button = WebDriverWait(driver, 2).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[3]/div/div[1]/div[1]/a/div[1]/div[2]'))
    )
    actions = ActionChains(driver)
    actions.move_to_element(click_button).perform()
    driver.execute_script("arguments[0].click();", click_button)
    time.sleep(10)
    comment_elements = driver.find_elements(By.XPATH, '/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/div[1]/div/article/div/div[2]/div/div[2]/div[1]/ul/div/div/div/div/ul/div/li/div/div/div[2]/div[1]/span')
    for comment in comment_elements:
        print(comment.text)
    driver.quit()


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
        time.sleep(2)
        facebook_caption=driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[2]/div/div/div[3]/div[1]/div/div/div/span/div[1]/div")
        facebook_caption=facebook_caption.text
        actions.move_to_element(comments_button).perform()
        driver.execute_script("arguments[0].click();", comments_button)
        time.sleep(2) 
        comment_elements = driver.find_elements(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div/div[2]/div[3]/div/div/div/div/div[1]/div[2]/div[1]/div[1]/div/div/div/div/div/span") 
        cursor = connection.cursor()
        cursor.execute("SELECT caption,comment FROM comments WHERE email = %s and  type= %s ORDER BY id DESC", (session['email'], 'facebook'))
        details = cursor.fetchall()
        if details: 
            for row in details:
                caption = row[0]
                comment = row[1]
                flag=0
                print(caption,comment)
                if comment.strip() != comment_elements[0].text.strip():
                    for comment in comment_elements:
                        if sentimental_analysis(comment.text):
                            cursor = connection.cursor()
                            cursor.execute("INSERT INTO comments (email, caption, comment, type) VALUES (%s, %s, %s, %s)", 
                                        (session['email'], facebook_caption, comment.text, 'facebook'))
                            connection.commit()
                            cursor.close() 
                            flag=1
                            break
                        else:
                            flag=1
                            break
                    if flag==1:
                        break
                else:
                    break
        elif not details:
            for comment in reversed(comment_elements):
                if sentimental_analysis(comment.text):
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO comments (email, caption, comment, type) VALUES (%s, %s, %s, %s)", 
                                (session['email'], facebook_caption, comment.text, 'facebook'))
                    connection.commit()
                    cursor.close()
                else:
                    continue
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        return True

@app.route('/facebook')
def facebook():
        print("I am in facebook")
        email=session['email']
        type='facebook'
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT caption,comment FROM comments WHERE email = %s and  type= %s", (email, type))
            details = cursor.fetchall()
            comments_list = []
            if details:
                for detail in details:
                    caption = detail[0] 
                    comment = detail[1]  
                    comments_list.append({'caption': caption, 'comment': comment})
                print('-----------------------------------------------------------------------------------------------------')
            return render_template('facebook.html', comments_list=comments_list)
        except Exception as e:
            print(e)
            return render_template('index.html',msg="Something went wrong. Please try again")
        finally:
            cursor.close()

@app.route('/develop')
def develop():
    return render_template('develop.html')

if __name__ == '__main__':
    app.run(debug=True)