"""Open a separate visible Chrome profile, authenticated as the demo KSGS."""
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

local = Path(__file__).resolve().parent / '.local'
secrets = json.loads((local / 'credentials.json').read_text(encoding='utf-8-sig'))
options = webdriver.ChromeOptions()
options.add_experimental_option('detach', True)
options.add_argument('--user-data-dir=' + str(local / 'open-profile'))
options.add_argument('--no-first-run')
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)
driver.get('http://127.0.0.1:8079/web/login')
wait = WebDriverWait(driver, 60)
if driver.find_elements(By.NAME, 'login'):
    driver.find_element(By.NAME, 'login').send_keys('ksgs.demo')
    driver.find_element(By.NAME, 'password').send_keys(secrets['ksgs'])
    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.o_web_client')))
driver.get('http://127.0.0.1:8079/web#action=dtc_bts_base.action_dtc_bts_project')
wait.until(lambda d: 'DEMO-LIVE' in d.find_element(By.TAG_NAME, 'body').text)
main = driver.current_window_handle
driver.switch_to.new_window('tab')
driver.get('http://127.0.0.1:8025')
wait.until(lambda d: 'Mailpit' in d.title)
driver.switch_to.window(main)
driver.service.stop()
print('Opened visible Chrome: KSGS project list and Mailpit. Browser remains open.')
