from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

__author__ = 'PLNech'


def zoom_out(driver):
    html = driver.find_element(By.TAG_NAME, "html")
    html.send_keys(Keys.CONTROL, '-')
    html.send_keys(Keys.CONTROL, '-')
    html.send_keys(Keys.CONTROL, '-')


def screenshot_step(driver, screen_prefix, step_number):
    step_filename = screen_prefix + " - step%d.png" % step_number
    retval = driver.save_screenshot(step_filename)
    print("Saving screenshot %d as %s..." % (step_number, step_filename),
          "Success" if retval else "Error")
