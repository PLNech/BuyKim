from datetime import datetime
import time
import os
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import zoom_out

DEBUG = True

# ref_product = "143sys2"
ref_product = "150sk22" if DEBUG else "150sk20"
ref_zone = "gra" if DEBUG else "bhs"
not_available_terms = ['unknown', 'unavailable']

available = False
while not available:
    print("Requesting...", flush=True, end=' ')
    request_ws = requests.get("https://ws.ovh.com/dedicated/r2/ws.dispatcher/getAvailability2")
    data = request_ws.json()

    available_servers = data['answer']['availability']
    if 'answer' in data:
        if 'availability' in data['answer']:
            found_product = False
            for line in available_servers:
                if line['reference'] == ref_product:
                    found_product = True

                    found_zone = False
                    for zone in line['zones']:
                        if zone['zone'] == ref_zone:
                            found_zone = True
                            availability = zone['availability']
                            available = availability not in not_available_terms
                            available_status = ("" if available else "not ") + "available"
                            print('Model %s in dc %s is marked as %s -> %s' % (
                                ref_product, ref_zone, availability, available_status))
                            if available:
                                break
                            else:
                                continue
                    if not found_zone:
                        print("Zone %s was not found in data about product %s." % (ref_zone, ref_product))
            if not found_product:
                print("No data about product %s." % ref_product)
    else:
        print("No answer in ws data.")
print("Exited availability loop, %s is available in %s!" % (ref_product, ref_zone))


time_run = datetime.now().strftime("%y-%m-%d %H-%m-%f")
screenshot_dir = os.getenv("SCREENSHOT_DIR", os.path.abspath("screens")) + "\\"
print("Saving screenshots in %s" % screenshot_dir)
screen_prefix = screenshot_dir + time_run

step1_filename = screen_prefix + " - step1.png"
step2_filename = screen_prefix + " - step2.png"
step3_filename = screen_prefix + " - step3.png"

ovh_user = os.environ["OVH_USERNAME"]
ovh_pass = os.environ["OVH_PASSWORD"]

print("Loaded environment: Connecting as %s with password %s..." % (ovh_user, ovh_pass[:5]))

driver = webdriver.Firefox()
driver.maximize_window()
available = False
driver.get("https://www.kimsufi.com/fr/commande/kimsufi.xml?reference=" + ref_product)
# driver.get("https://eu.soyoustart.com/fr/commande/soYouStart.xml?reference=143sys2")
try:
    # assert "Kimsufi" in driver.title
    zoom_out(driver)
    # Wait for the removal of waiting banner...
    WebDriverWait(driver, 10).until_not(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.fixed-header div.alert.alert-info.ng-scope")))
    print("Page finished loading.")
except AssertionError:
    print("The page didn't load correctly.")

    # if driver.find_element_by_class_name("alert-error") is None:
    #     available = True

js_select_dhs = """var appDom = document.querySelector('#quantity-1');
var appNg = angular.element(appDom);
var scope = appNg.scope();
scope.config.datacenter = 'bhs';
scope.$apply();
"""

print("Executing select script: `%s`." % js_select_dhs)
driver.execute_script(js_select_dhs)
print("Selected canadian datacenter.")

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
# Locate login inputs
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
driver.save_screenshot(step3_filename)
time.sleep(10)
if DEBUG:
    driver.close()
