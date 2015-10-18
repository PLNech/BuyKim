from datetime import datetime
import os
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import zoom_out

DEBUG = True

time_run = datetime.now().strftime("%y-%m-%d %H-%m-%f")
screenshot_dir = os.getenv("SCREENSHOT_DIR", os.path.abspath("screens")) + "\\"
print("Saving screenshots in %s" % screenshot_dir)
screen_prefix = screenshot_dir + time_run

step1_filename = screen_prefix + " - step1.png"
step2_filename = screen_prefix + " - step2.png"
step3_filename = screen_prefix + " - step3.png"

ref_product = "150sk22" if DEBUG else "150sk20"
ovh_user = os.environ["OVH_USERNAME"]
ovh_pass = os.environ["OVH_PASSWORD"]

print("Loaded environment: Connecting as %s with password %s..." % (ovh_user, ovh_pass[:5]))

driver = webdriver.Firefox()
available = False
while not available:
    available = True
    # driver.get("https://www.kimsufi.com/fr/commande/kimsufi.xml?reference=" + ref_product)
    driver.get("https://eu.soyoustart.com/fr/commande/soYouStart.xml?reference=143sys2")
    try:
        # assert "Kimsufi" in driver.title
        zoom_out(driver)
        WebDriverWait(driver, 10).until_not(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.fixed-header div.alert.alert-info.ng-scope")))
        print("Page finished loading.")
    except AssertionError:
        print("The page didn't load correctly.")

    # if driver.find_element_by_class_name("alert-error") is None:
    #     available = True

css_dc_header = "div.dedicated-configuration-and-resume tr.editable.last td.first label"
css_dc_fr = "input#dc-default"
css_dc_bhs = "input#dc-bhs"
# header_dc = driver.find_element_by_css_selector(css_dc_bhs)
selector_dc = driver.find_element_by_css_selector(css_dc_bhs)

ActionChains(driver).move_to_element(selector_dc).perform()
print("Moved to DC header.")
time.sleep(1)
selector_dc.click()
time.sleep(1)
selector_dc = driver.find_element_by_css_selector(css_dc_fr)
selector_dc.click()
time.sleep(1)
selector_dc = driver.find_element_by_css_selector(css_dc_bhs)
selector_dc.click()
time.sleep(3)
print("Clicked on canadian datacenter.")
# FIXME: How can I activate this input?

css_label_existing = "span.existing label"
css_button_login = "div.customer-existing form span.last.ec-button span button"

id_input_login = "existing-customer-login"
id_input_pass = "existing-customer-password"

# Check existing customer
button_existing = driver.find_element_by_css_selector(css_label_existing)
print("Button found: ", button_existing)

button_existing.click()
print("Clicked on existing customer.")

driver.execute_script("arguments[0].scrollIntoView(true);", button_existing)
driver.save_screenshot(step1_filename)
# Wait for page reaction, then locate login inputs
input_login = driver.find_element_by_id(id_input_login)
input_pass = driver.find_element_by_id(id_input_pass)

# Connect with given credentials
input_login.send_keys(ovh_user)
input_pass.send_keys(ovh_pass)
print("Wrote username and password into inputs.")
driver.find_element_by_css_selector(css_button_login).click()
print("Clicked on login button.")
retval = driver.save_screenshot(step2_filename)
print("Saving screenshot 2 as %s..." % step2_filename,
      "Success" if retval else "Error")


# Wait for means of payment to load
css_payment_valid = "div.payment-means-choice div.payment-means-list form span.selected input.custom-radio.ng-valid"
WebDriverWait(driver, 20).until(EC.presence_of_element_located(
    (By.CSS_SELECTOR, css_payment_valid)
))

# Check inputs to accept contract conditions
css_input_cgv = "div.dedicated-contracts input#contracts-validation"
css_input_custom = "div.dedicated-contracts input#customConractAccepted"
css_button_purchase = "div.dedicated-contracts button.centered"
driver.find_element_by_css_selector(css_input_cgv).click()
driver.find_element_by_css_selector(css_input_custom).click()
print("Checked confirmation inputs.")

if not DEBUG:
    # BIG RED BUTTON! DON'T UNCOMMENT UNTIL YOU ARE DAMN SURE
    # driver.find_element_by_css_selector(css_input_cgv).click()
    pass


# Wait to realise what you've done
driver.implicitly_wait(15)
driver.save_screenshot(step3_filename)
if DEBUG:
    driver.close()
