from datetime import datetime
import time
import os
import logging
import traceback

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import click

from utils import zoom_out, screenshot_step


def print_and_log(message, level=logging.INFO, sep=' ', end='\n', flush=False):
    print(message, sep=sep, end=end, flush=flush)
    logging.log(level, message)


@click.command()
@click.option('--timeout-conn', '-t', default=5, show_default=True, help='Maximum time in seconds to wait for webservice answer.')
@click.option('--interval', '-i', default=7.5, show_default=True, help='Minimum interval in seconds between two requests')
@click.option('--product-family', default="Kimsufi", show_default=True, help='The family of servers (ie. "Kimsufi"/"So you Start")')
@click.option('--ref-product', '-p', default="1801sk12", show_default=True, help='Reference of the server (ie 1801sk12 for KS1, 1801sys29 for some soYouStart servers')
@click.option('--ref-zones', '-z', default=["gra","rbx","lon","fra"], show_default=True, multiple=True, help='Data center short name(s) (ie "-z gra -z rbx")')
@click.option('--quantity', '-q', default=1, show_default=True, help='Number of servers to rent - 1 to 5 (Maximum)')
@click.option('--payment-frequency', '-f', default=1, show_default=True, help='Receive the bill every 1,3,6 or 12 month')
@click.option('--ovh-user', prompt=True, hide_input=False)
@click.option('--ovh-pass', prompt=True, hide_input=True)
@click.option('--debug/--no-debug', default=False, help='Debug mode, disable by default. Add --debug flag to enable')
def main(timeout_conn, interval, product_family, ref_product, ref_zones, quantity, payment_frequency, ovh_user, ovh_pass, debug):

    # Check input is correct
    possible_payment_frequency = [1,3,6,12]
    if payment_frequency not in possible_payment_frequency:
        raise IOError('Error: possible choices for the billing frequency are 1,3,6 or 12 months. You entered "--payment-frequency {}"'.format(payment_frequency))
    if quantity not in [1,2,3,4,5]:
        raise IOError('Error: It is only possible to order 1 to 5 at once. You entered "--quantity {}"'.format(quantity))

    # define constants
    MAX_REQ_TIMEOUT_READ = None
    url_availability = "https://ws.ovh.com/dedicated/r2/ws.dispatcher/getAvailability2"
    not_available_terms = ['unknown', 'unavailable']

    time_run = datetime.now().strftime("%y-%m-%d %H-%M-%f")

    screenshot_dir = os.getenv("SCREENSHOT_DIR", os.path.abspath("screens"))
    log_dir = os.getenv("LOG_DIR", os.getcwd())
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, "buyKim.log")

    print("Log filename: {}".format(log_filename))
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', filename=log_filename, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)

    print_and_log("Saving screenshots in {}".format(screenshot_dir))
    screen_prefix = screenshot_dir + time_run

    available = False
    while not available:
        success = False
        time_start = time.time()
        time_elapsed = 0
        time_run_str = datetime.now().strftime("%y/%m/%d %H:%M:%S")
        log_msg = "Requesting... "
        print("{} | {} ".format(time_run_str, log_msg), flush=True)
        try:
            request_ws = requests.get(url_availability, timeout=(timeout_conn, MAX_REQ_TIMEOUT_READ))
            data = request_ws.json()

            if 'answer' in data:
                if 'availability' in data['answer']:
                    available_servers = data['answer']['availability']
                    found_product = False
                    for line in available_servers:
                        if line['reference'] == ref_product:
                            found_product = True

                            found_zone = None
                            msg_model = ""
                            msg_zones = "zones:"
                            zone_avails = []
                            for zone in line['zones']:
                                availability = zone['availability']
                                zone_name = zone['zone']
                                zone_avails.append(zone_name + "=" + availability)
                                if zone_name in ref_zones:
                                    found_zone = zone_name
                                    success = True
                                    available = availability not in not_available_terms
                                    msg_model = 'The status of model "{}" in dc "{}" is {}'.format(ref_product, zone_name, availability)
                                    log_msg += msg_model
                                    print_and_log(msg_model)
                                    if available:
                                        break

                            print_and_log("None of the zones was available ({})".format(", ".join(zone_avails)))
                            if not found_zone:
                                print_and_log("None of the data center was found for product {}.".format(', '.join(ref_zones), ref_product))
                    if not found_product:
                        print_and_log("No data about product {}.".format(ref_product))
            else:
                print_and_log("No answer in ws data.")
        except TimeoutError:
            print_and_log("Timeout while fetching webservice.")
        except Exception as e:
            print_and_log(str(type(e)) + " while parsing: " + str(e.args) + ' | ' + "Data: " + str(data))
            with open(log_filename, mode='a') as f:
                f.write("\n" + "-" * 60)
                traceback.print_exc(file=f)
                f.write("-" * 60 + "\n")
        while time_elapsed < interval:
            time_end = time.time()
            time_elapsed = time_end - time_start
            time.sleep(1)
        msg_time = " (time: %f)" % time_elapsed
        if success:
            print(msg_time)
        logging.log(logging.DEBUG, log_msg + msg_time)

    print_and_log("Exited availability loop, {} is available in {}!".format(ref_product, found_zone))

    driver = webdriver.Firefox()
    driver.maximize_window()
    available = False
    driver.get("https://www.kimsufi.com/fr/commande/kimsufi.xml?reference=" + ref_product)
    # driver.get("https://eu.soyoustart.com/fr/commande/soYouStart.xml?reference=143sys2")
    try:
        assert product_family in driver.title
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
    scope.config.datacenter = '{}';
    scope.$apply();
    """.format(found_zone)

    print_and_log("""Executing select script:
    {}
    """.format(js_select_dhs))
    driver.execute_script(js_select_dhs)
    print_and_log("Selected {} datacenter.".format(found_zone))

    # Select quantity and payment options
    selecor_quantity_line = driver.find_element_by_css_selector('tbody.configuration tr:nth-child(2)')
    selector_quantity = driver.find_element_by_css_selector('tbody.configuration tr:nth-child(2) li:nth-child({})'.format(quantity))
    Hover = ActionChains(driver).move_to_element(selecor_quantity_line).move_to_element(selector_quantity)
    Hover.click().perform()
    print_and_log("Selected to rent {} servers.".format(quantity))

    # possible_payment_frequency index + 1 gives the option number to pick
    option = possible_payment_frequency.index(payment_frequency) + 1
    selecor_frequency_line = driver.find_element_by_css_selector('tbody.configuration tr:nth-child(3)')
    selector_frequency = driver.find_element_by_css_selector('tbody.configuration tr:nth-child(3) li:nth-child({})'.format(option))
    Hover = ActionChains(driver).move_to_element(selecor_frequency_line).move_to_element(selector_frequency)
    Hover.click().perform()
    print_and_log("Selected to rent servers for {} months.".format(payment_frequency))

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
    if not debug:
        driver.find_element_by_css_selector(css_button_purchase).click()
        print_and_log("Clicked on purchase button...")

    # Wait to realise what you've done
    screenshot_step(driver, screen_prefix, 4)
    time.sleep(30)
    screenshot_step(driver, screen_prefix, 5)
    if debug:
        driver.close()


if __name__ == '__main__':
    main()
