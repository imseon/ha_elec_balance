from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from PIL import Image
from io import BytesIO
import base64
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.alert import Alert
import requests
import shutil
import os
import urllib3
import json

DAMAGOU_USER = ''  # 打码狗平台账号
DAMAGOU_PASS = ''  # 打码狗平台密码

SITE_USER = ''  # 电网平台账号
SITE_PASS = ''  # 电网平台密码

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-data-dir=data')
options.add_experimental_option(
    "excludeSwitches", ['enable-automation'])
options.set_capability('unhandledPromptBehavior', 'accept')

driver = None
wait = None
maxTry = 5
tryCount = 0
screenshot_path = os.environ['screenshot_path'] if 'screenshot_path' in os.environ else ''

def initDriver():
    global driver
    global wait
    try:
        shutil.rmtree('./data')
    except FileNotFoundError:
        pass
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    wait = WebDriverWait(driver, 10)


def log(*args):
    print('[' + time.strftime("%Y-%m-%d %H:%M:%S",
                              time.localtime()) + ']', ' '.join(args))


def getCaptcha():
    global driver
    global DAMAGOU_USER
    global DAMAGOU_PASS
    png = driver.get_screenshot_as_png()
    im = Image.open(BytesIO(png))
    img_size = im.size
    scale = img_size[0] / 1920
    el_captcha = driver.find_element(By.CSS_SELECTOR, '.code-mask')
    location = el_captcha.location
    size = el_captcha.size

    left = location['x'] * scale
    top = location['y'] * scale
    right = left + size['width'] * scale
    bottom = top + size['height'] * scale

    im = im.crop((left, top, right, bottom))
    buffered = BytesIO()
    im.save('captcha.png')
    im.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())

    log('begin to request damagou')
    try:
        r = requests.get('http://www.damagou.top/apiv1/login.html', params={
            'username': DAMAGOU_USER,
            'password': DAMAGOU_PASS
        }, timeout=10)
    except urllib3.exceptions.ReadTimeoutError:
        log('request damagou timeout, retry')
        return getCaptcha()
    except requests.exceptions.ReadTimeout:
        log('request damagou timeout, retry')
        return getCaptcha()

    user_key = r.content

    try:
        r = requests.post('http://www.damagou.top/apiv1/recognize.html', data={
            'image': img_str,
            'userkey': user_key
        }, timeout=10)
    except urllib3.exceptions.ReadTimeoutError:
        log('request damagou timeout, retry')
        return getCaptcha()
    except requests.exceptions.ReadTimeout:
        log('request damagou timeout, retry')
        return getCaptcha()
    log('got response from damagou')

    captcha = bytes.decode(r.content)
    return captcha


def login():
    global driver
    global SITE_USER
    global SITE_PASS
    global tryCount
    global maxTry
    global screenshot_path
    tryCount += 1
    try:
        driver.get("https://www.95598.cn/osgweb/login")
    except TimeoutException:
        log('open login page timeout, retry:', str(tryCount))
        if tryCount < maxTry:
            return login()
        else:
            return False
    log('opened page: ', driver.current_url)
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".selectlogin-type .user"))
    )
    try:
        el_switch = driver.find_element(By.CSS_SELECTOR, '.selectlogin-type .user')
        el_switch.click()
        time.sleep(1)
        el_username = driver.find_element(By.CSS_SELECTOR, '.password_form .el-form-item:nth-child(1) input')
        el_username.send_keys(SITE_USER)
        el_password = driver.find_element(By.CSS_SELECTOR, '.password_form .el-form-item:nth-child(2) input')
        el_password.clear()
        el_password.send_keys(SITE_PASS)
        log('ready to recognize captcha')
        captcha = getCaptcha()
        log('recognized captcha:', captcha)
        el_captcha = driver.find_element(By.CSS_SELECTOR, '.password_form .el-form-item:nth-child(3) input')
        el_captcha.send_keys(captcha)
        driver.find_element(By.CSS_SELECTOR, '.input-login-area:nth-child(1) button').click()
        log('submit login')
        time.sleep(3)
        log('redirected:', driver.current_url)
        driver.save_screenshot(screenshot_path + 'login.png')
        log('login screenshot has been taken')
        if '/login' not in driver.current_url:
            return True
        if tryCount < maxTry:
            return login()
        else:
            return False
    except:
        driver.save_screenshot(screenshot_path + 'login.png')
        log('login screenshot has been taken')
        if tryCount < maxTry:
            return login()
        else:
            return False 

def getBalance():
    global driver
    global wait
    global tryCount
    global maxTry
    global screenshot_path
    tryCount += 1
    try:
        driver.get(
            'https://www.95598.cn/osgweb/userAcc')
        log('opened balance page:', driver.current_url)
        if '/login' in driver.current_url:
            return None
    except TimeoutException:
        log('get balance timeout. retry:', str(tryCount))
        driver.save_screenshot(screenshot_path + 'account.png')
        log('account screenshot has been taken')
        time.sleep(5)
        if tryCount < maxTry:
            return getBalance()
        else:
            return None
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".acccount .amt:nth-child(1) .num"))
        )
        balance = driver.find_element(By.CSS_SELECTOR, 
            '.acccount .amt:nth-child(1) .num').text
        return balance
    except TimeoutException:
        log('get balance timeout. retry:', str(tryCount))
        driver.save_screenshot(screenshot_path + 'account.png')
        log('account screenshot has been taken')
        time.sleep(5)
        if tryCount < maxTry:
            return getBalance()
        else:
            return None


def writeToFile(balance):
    dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir, 'balance')
    log('write to:', file_path)
    f = open(file_path, 'w')
    f.write(balance)
    f.close()


def fetchBalance():
    global driver
    global tryCount
    global maxTry
    initDriver()
    driver.set_window_size(1920, 1080)
    log('resize window to 1920*1080')
    # driver.get('https://www.95598.cn/osgweb/my95598')
    # time.sleep(10)
    # driver.save_screenshot(screenshot_path + 'my95598.png')
    # log('my95598 screenshot has been taken')
    # time.sleep(10)
    tryCount = 0
    if login():
        log('login success')
        time.sleep(1)
        tryCount = 0
        balance = getBalance()
        if balance:
            log('got balance:', balance)
            writeToFile(json.dumps({'balance': balance, 'updated_at': time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime())}))
        else:
            log('get balance failed.')
    else:
        log('login failed.')
        

try:
    fetchBalance()
finally:
    driver.quit()
    log('done.')
