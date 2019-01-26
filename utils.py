import os
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

__author__ = 'PLNech'


def zoom_out(driver):
    html = driver.find_element(By.TAG_NAME, "html")
    html.send_keys(Keys.CONTROL, '-')
    html.send_keys(Keys.CONTROL, '-')
    html.send_keys(Keys.CONTROL, '-')


def screenshot_step(driver, screen_path, step_number):
    file_name = "{:%Y-%m-%d-%H-%M-%S}-step{}.png".format(datetime.now(), step_number)
    screenshot_full_path = os.path.realpath(os.path.join(screen_path, file_name))
    retval = driver.save_screenshot(screenshot_full_path)
    print("Saving screenshot {} as {}...".format(step_number, screenshot_full_path),
          "Success" if retval else "Error")
