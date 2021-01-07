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
    el_captcha = driver.find_element_by_id('imgVcode')
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
    try:
        driver.get("http://www.95598.cn/member/login.shtml")
    except TimeoutException:
        log('open login page timeout, retry')
        return login()
    log('opened page: ', driver.current_url)
    el_username = driver.find_element_by_id('loginName')
    el_username.send_keys(SITE_USER)
    el_password = driver.find_element_by_id('txPwd')
    el_password.click()
    el_password = driver.find_element_by_id('pwd')
    el_password.clear()
    el_password.send_keys(SITE_PASS)
    log('ready to recognize captcha')
    captcha = getCaptcha()
    log('recognized captcha:', captcha)
    # driver.find_element_by_id('imgVcode').click()
    el_captcha = driver.find_element_by_id('code')
    el_captcha.send_keys(captcha)
    driver.find_element_by_class_name('submitBtn').click()
    log('submit login')
    driver.save_screenshot('index.png')
    try:
        WebDriverWait(driver, 3).until(EC.text_to_be_present_in_element(
            (By.ID, "loginMsg"), '验证码错误，请重新输入!'))
        log('captcha error, attempt to relogin 5 seconds later')
        time.sleep(5)
        return login()
    except TimeoutException:
        return
    except AttributeError:
        return
    except UnexpectedAlertPresentException:
        return


def getBalance():
    global driver
    global wait
    try:
        driver.get(
            'http://www.95598.cn/95598/per/account/initSmartConsInfo?partNo=PM02001007')
        log('opened balance page:', driver.current_url)
    except TimeoutException:
        log('open balance page timeout. will retry in 5 seconds')
        time.sleep(5)
        return getBalance()
    except UnexpectedAlertPresentException:
        log('alert exception. will retry in 5 seconds')
        time.sleep(5)
        return getBalance()

    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#smartTable tbody tr:nth-child(1) td:nth-child(3)"))
        )
        balance = driver.find_element_by_css_selector(
            '#smartTable tbody tr:nth-child(1) td:nth-child(3)').text
        return balance
    except TimeoutException:
        log('get balance timeout')
        return getBalance()


def writeToFile(balance):
    dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir, 'balance')
    log('write to:', file_path)
    f = open(file_path, 'w')
    f.write(balance)
    f.close()


def fetchBalance():
    global driver
    initDriver()
    driver.set_window_size(1920, 1080)
    log('resize window to 1920*1080')
    login()
    log('login success')
    time.sleep(3)
    balance = getBalance()
    log('got balance:', balance)
    if balance:
        writeToFile(json.dumps({'balance': balance, 'updated_at': time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime())}))
    return balance


try:
    fetchBalance()
finally:
    driver.quit()
