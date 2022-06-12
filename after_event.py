# %%
import pymysql
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# get environment variables (need to be set on the server or function that is used)
db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASS')
cms_user = os.environ.get('CMS_USER')
cms_pass = os.environ.get('CMS_PASS')

# set up webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')

# driver = webdriver.Chrome(executable_path='/home/ubuntu/lsc/chromedriver', chrome_options=chrome_options,
#   service_args=['--verbose', '--log-path=/tmp/chromedriver.log'])

# s=Service(r"/Users/gisbertgurke/Desktop/chromedriver")
# driver = webdriver.Chrome(service=s)

driver = webdriver.Chrome(chrome_options=chrome_options, service=Service(ChromeDriverManager().install()))
driver.implicitly_wait(20)

# connect to db
conn = pymysql.connect(host=db_host,
                       user=db_user,
                       password=db_pass)

c = conn.cursor()
c.execute('''USE testdatabase''')

# check for MySQL database changes (this is just a draft)

# def DatabaseChanges():
#     most_recent_db_event = c.execute(SELECT timestamp FROM lsc_events ORDER BY timestamp DESC LIMIT 1;)

#     if most_recent_db_event > datetime.now (?) – 60min (?):
#         run the script […]

# get HTML block from db
c.execute('''SELECT html_insert FROM lsc_events WHERE id > 0''')
html_insert = c.fetchall()

# add some HTML blocks together as a test
full_html = ["<p><a href=\"Past-Events/index.html\">Past events</a></p>"]
for element in html_insert:
    html_section = element[0]
    full_html.append(html_section)

final_html = "".join(full_html)
final_html = final_html + "<hr />"

# gets CMS login page, logs in
driver.get("https://cms.fu-berlin.de/cmslogin/")
username_input_field = driver.find_element(By.XPATH, "//input[@id='login']")
username_input_field.click()
username_input_field.send_keys(cms_user)
password_input_field = driver.find_element(By.XPATH, "//input[@id='password']")
password_input_field.click()
password_input_field.send_keys(cms_pass)
password_input_field.send_keys(Keys.RETURN)

delay = 15

try:
    iframe_cms_subpages = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, '/html/body/table/tbody/tr[2]/td[1]/iframe')))
    print("iframe found!")
except TimeoutException:
    print("Loading took too much time or the window was open.")

#iframe_cms_subpages = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td[1]/iframe')
driver.switch_to.frame(iframe_cms_subpages)

print("success! switched to iframe")

# close jura menu if necessary
try:
    jura_main_menu = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='npsLogic_nodeViewEntry_c_/jura_npsLogic']/img[@alt='-']")))
    print("Jura menu open! Close it first")
    jura_main_menu.click()
    print("closed!")
except TimeoutException:
    print("Menu was either already closed or something went wrong.")

# switch to parent frame and back to iframe, otherwise a bug prevents further actions 
driver.switch_to.parent_frame()
try:
    iframe_cms_subpages = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, '/html/body/table/tbody/tr[2]/td[1]/iframe')))
    print("iframe found!")
except TimeoutException:
    print("Loading took too much time or the window was open.")

driver.switch_to.frame(iframe_cms_subpages)

# open LSC menu if necessary
try:
    lsc_main_menu = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='npsLogic_nodeViewEntry_e_/laws-of-social-cohesion_npsLogic']/img[@alt='+']")))
    print("LSC menu closed! Needs to be opened first")
    lsc_main_menu.click()
    print("LSC menu opened!")
except TimeoutException:
    print("Menu was either already open or something went wrong.")

driver.switch_to.parent_frame()

try:
    iframe_cms_subpages = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, '/html/body/table/tbody/tr[2]/td[1]/iframe')))
    print("iframe found!")
except TimeoutException:
    print("Loading took too much time or the window was open.")
driver.switch_to.frame(iframe_cms_subpages)

print("Now the LSC menu should be open!")

#click on events section
try:
    events_section = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//td[normalize-space()='Events']")))
    print("events section detected")
    events_section.click()
    print("events section clicked!")
except TimeoutException:
    print("Loading events section took too long.")

# switch back to parent. This is because of the hierarchy of iframes here
driver.switch_to.parent_frame()

# detect Eigenschaften iframe and switch to it

try:
    inspector_iframe = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.NAME, 'nps_inspector_frame')))
    print("inspector frame found!")
    driver.switch_to.frame(inspector_iframe)
    print("switched to inspector frame")
except TimeoutException:
    print("Loading inspector frame took too much time.")


try:
    eigenschaften_iframe = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.NAME, 'nps_value_frame')))
    print("eigenschaften frame found!")
    driver.switch_to.frame(eigenschaften_iframe)
    print("switched to eigenschaften frame")
except TimeoutException:
    print("Loading eigenschaften frame took too much time.")

# save current window handle to be able to switch back later
window_0 = driver.window_handles[0]
    
# click "alle bearbeiten"
try:
    alle_bearbeiten_button = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, '//input[@value=\'Alle bearbeiten\']')))
    print("found alle bearbeiten")
    alle_bearbeiten_button.click()
    print("clicked alle bearbeiten")
except TimeoutException:
    print("alle bearbeiten took too long to load.")
    
# save new window handle and switch to it
window_1 = driver.window_handles[1]
driver.switch_to.window(window_1)
print("switched to window 1!")

# switch to another iframe
try:
    edit_iframe = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.NAME, 'editFrame')))
    print("edit frame found!")
    driver.switch_to.frame(edit_iframe)
    print("switched to edit frame")
except TimeoutException:
    print("Loading edit_frame took too much time.")

# click "Hauptinhalt bearbeiten"   
try:
    hauptinhalt_bearbeiten = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='userInput.blob.edit']")))
    print("hauptinhalt bearbeiten button detected")
    hauptinhalt_bearbeiten.click()
    print("hauptinhalt bearbeiten button clicked!")
except TimeoutException:
    print("Loading hauptinhalt bearbeiten button took too long.")

# click insert HTML button
try:
    insert_HTML_button = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//span[@class='mceIcon mce_code']")))
    print("insert_HTML button detected")
    insert_HTML_button.click()
    print("insert_HTML button clicked!")
except TimeoutException:
    print("Loading insert_HTML_button took too long.")

window_2 = driver.window_handles[2]
driver.switch_to.window(window_2)
print("switched to window 2!")

try:
    html_textarea = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//textarea[@id='htmlSource']")))
    print("html_textarea detected")
    html_textarea.clear()
    html_textarea.send_keys(final_html)
    print("insert_HTML button clicked!")
except TimeoutException:
    print("Loading insert_HTML_button took too long.")

# click submit button

def click_submit_button():
    try:
        submit_button = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Update']")))
        print("submit button detected")
        submit_button.click()
        print("submit button clicked!")
    except TimeoutException:
        print("Loading submit button took too much time.")
click_submit_button()

driver.switch_to.window(window_1)

#driver.switch_to.parent_frame()

# click okay button

def click_okay_button():
    try:
        okay_button = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='submit npsLogic_submit_userInput.okButton_npsLogic']")))
        print("okay button detected")
        okay_button.click()
        print("okay button clicked!")
    except TimeoutException:
        print("Loading okay button took too much time.")
click_okay_button()

click_okay_button()

# log out of CMS

def log_out_of_cms():
    try:
        log_out_button = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, "//img[@title='Von Fiona abmelden']")))
        print("log out button detected")
        log_out_button.click()
        print("log out button clicked!")
    except TimeoutException:
        print("Loading log out button took too much time.")

driver.switch_to.window(window_0)
log_out_of_cms()

driver.quit()
# send log info to streamlit once I have built the dashboard

# %%
