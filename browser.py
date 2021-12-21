import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_cookies():
    options = Options()
    options.headless = True

    driver = webdriver.Chrome('./chromedriver', options=options)

    driver.get("https://www.timeform.com/horse-racing/account/sign-in?returnUrl=%2Fhorse-racing%2F")

    time.sleep(3)
    cookie_btn = driver.find_element(by=By.XPATH, value="/html/body/div/div/button")
    cookie_btn.click()
    time.sleep(1.5)

    email_input = driver.find_element(by=By.ID, value="EmailAddress")
    email_input.send_keys("p.programist.kg@gmail.com")

    password_input = driver.find_element(by=By.ID, value="Password")
    password_input.send_keys("QNMr25BQ258")

    remember_me_input = driver.find_element(by=By.ID, value="RememberMe")
    remember_me_input.click()

    send_btn = driver.find_element(by=By.CSS_SELECTOR, value=".button")
    send_btn.click()
    time.sleep(3.5)

    cookies_data = driver.get_cookies()
    driver.close()

    cookies = {
        dct.get("name"): dct.get("value") for dct in cookies_data
    }

    return cookies