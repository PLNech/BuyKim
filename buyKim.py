from datetime import datetime
import time
import os
import logging

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import zoom_out, screenshot_step


def print_and_log(message, level=logging.DEBUG, sep=' ', end='\n', flush=False):
    print(message, sep=sep, end=end, flush=flush)
    logging.log(level, message)


MAX_REQ_TIMEOUT_READ = None

MAX_REQ_TIMEOUT_CONN = 5  # Maximum time in seconds to wait for webservice answer
MIN_REQ_INTERVAL = 5  # Minimum interval in seconds between two requests
DEBUG = True

page_title = "Kimsufi"  # "So you Start"
# ref_product = "143sys2"
ref_product = "150sk22" if DEBUG else "150sk20"
ref_zone = "gra" if DEBUG else "bhs"
url_availability = "https://ws.ovh.com/dedicated/r2/ws.dispatcher/getAvailability2"
not_available_terms = ['unknown', 'unavailable']

time_run = datetime.now().strftime("%y-%m-%d %H-%M-%f")

screenshot_dir = os.getenv("SCREENSHOT_DIR", os.path.abspath("screens")) + "\\"
log_dir = os.getenv("LOG_DIR", os.getcwd())
if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = os.path.join(log_dir, "buyKim.log")

print("Log filename: %s" % log_filename)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', filename=log_filename, level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)

print_and_log("Saving screenshots in %s" % screenshot_dir, logging.INFO)
screen_prefix = screenshot_dir + time_run

ovh_user = os.environ["OVH_USERNAME"]
ovh_pass = os.environ["OVH_PASSWORD"]
print_and_log("Loaded environment: Connecting as %s with password %s..." % (ovh_user, ovh_pass[:5]))

data = ""
available = False
while not available:
    time_start = time.time()
    time_elapsed = 0
    time_run_str = datetime.now().strftime("%y/%m/%d %H:%M:%S")
    log_msg = "Requesting... "
    print("%s | " % time_run_str + log_msg, flush=True, end=' ')
    try:
        request_ws = requests.get(url_availability, timeout=(MAX_REQ_TIMEOUT_CONN, MAX_REQ_TIMEOUT_READ))
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
                                msg_model = 'Model %s in dc %s is marked as %s -> %s' % (
                                    ref_product, ref_zone, availability, available_status)
                                log_msg += msg_model
                                print(msg_model, end="")
                                if available:
                                    break
                                else:
                                    while time_elapsed < MIN_REQ_INTERVAL:
                                        time_end = time.time()
                                        time_elapsed = time_end - time_start
                                        time.sleep(1)
                                    msg_time = " (time: %f)" % time_elapsed
                                    print(msg_time)
                                    logging.log(logging.DEBUG, log_msg + msg_time)
                                    continue
                        if not found_zone:
                            print_and_log("Zone %s was not found in data about product %s." % (ref_zone, ref_product))
                if not found_product:
                    print_and_log("No data about product %s." % ref_product)
        else:
            print_and_log("No answer in ws data.")
    except TimeoutError:
        print_and_log("Timeout while fetching webservice.")
    except Exception as e:
        print_and_log(str(type(e)) + " while parsing: ", str(e.args), ' | ' + "Data: ", data)

print_and_log("Exited availability loop, %s is available in %s!" % (ref_product, ref_zone))

driver = webdriver.Firefox()
driver.maximize_window()
available = False
driver.get("https://www.kimsufi.com/fr/commande/kimsufi.xml?reference=" + ref_product)
# driver.get("https://eu.soyoustart.com/fr/commande/soYouStart.xml?reference=143sys2")
try:
    assert page_title in driver.title
    zoom_out(driver)
    # Wait for the removal of waiting banner...
    WebDriverWait(driver, 10).until_not(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.fixed-header div.alert.alert-info.ng-scope")))
    print_and_log("Page finished loading.")
except AssertionError:
    print_and_log("The page didn't load correctly: " + driver.title)

    # if driver.find_element_by_class_name("alert-error") is None:
    #     available = True

js_select_dhs = """var appDom = document.querySelector('#quantity-1');
var appNg = angular.element(appDom);
var scope = appNg.scope();
scope.config.datacenter = '""" + ref_zone + """';
scope.$apply();
"""

print_and_log("Executing select script: `%s`." % js_select_dhs)
driver.execute_script(js_select_dhs)
print_and_log("Selected canadian datacenter.")

css_label_existing = "span.existing label"
css_button_login = "div.customer-existing form span.last.ec-button span button"

id_input_login = "existing-customer-login"
id_input_pass = "existing-customer-password"

# Check existing customer
button_existing = driver.find_element_by_css_selector(css_label_existing)
print_and_log("Button found: " + str(button_existing))
button_existing.click()
print_and_log("Clicked on existing customer.")

screenshot_step(driver, screen_prefix, 1)
driver.execute_script("arguments[0].scrollIntoView(true);", button_existing)
screenshot_step(driver, screen_prefix, 2)
# Locate login inputs
input_login = driver.find_element_by_id(id_input_login)
input_pass = driver.find_element_by_id(id_input_pass)

# Connect with given credentials
input_login.send_keys(ovh_user)
input_pass.send_keys(ovh_pass)
print_and_log("Wrote username and password into inputs.")
driver.find_element_by_css_selector(css_button_login).click()
print_and_log("Clicked on login button.")

screenshot_step(driver, screen_prefix, 3)

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
print_and_log("Checked confirmation inputs.")

# uncommented after numerous tests
if not DEBUG:
    driver.find_element_by_css_selector(css_button_purchase).click()
    print_and_log("Clicked on purchase button...")

# Wait to realise what you've done
screenshot_step(driver, screen_prefix, 4)
time.sleep(30)
screenshot_step(driver, screen_prefix, 5)
if DEBUG:
    driver.close()
