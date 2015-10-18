from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

__author__ = 'PLNech'


def zoom_out(driver):
    html = driver.find_element(By.TAG_NAME, "html")
    html.send_keys(Keys.CONTROL, '-')
    html.send_keys(Keys.CONTROL, '-')
    html.send_keys(Keys.CONTROL, '-')
