"""Local Chrome UI smoke check; screenshots and credentials stay ignored."""
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

folder = Path(__file__).resolve().parent / '.local'
secrets = json.loads((folder / 'credentials.json').read_text(encoding='utf-8-sig'))
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1440,1000')
options.add_argument('--disable-gpu')
options.add_argument('--no-first-run')
report = []
driver = webdriver.Chrome(options=options)
try:
    for role in ('ksgs', 'bgd', 'infra'):
        driver.delete_all_cookies()
        driver.get('http://127.0.0.1:8079/web/login')
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.NAME, 'login'))).send_keys(role + '.demo')
        driver.find_element(By.NAME, 'password').send_keys(secrets[role])
        driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.o_web_client')))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.o_main_navbar')))
        targets = [('dtc_bts_base.action_dtc_bts_project', 'DEMO'),
                   ('dtc_bts_base.action_dtc_bts_station', 'DEMO-BTS-LIVE')] if role == 'ksgs' else [
            ('dtc_bts_contract.action_bts_contract_dashboard', 'Hợp đồng'),
            ('dtc_bts_contract.action_bts_contract_signature_batch' if role == 'bgd'
             else 'dtc_bts_contract.action_bts_contract_renewal',
             'KS-HĐ' if role == 'bgd' else 'DEMO-RENEWAL')]
        for index, (action, expected) in enumerate(targets):
            driver.get('http://127.0.0.1:8079/web#action=' + action)
            wait.until(lambda d: expected.lower() in d.find_element(By.TAG_NAME, 'body').text.lower())
            wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '.o_action_manager .o_content'))
            driver.save_screenshot(str(folder / ('ui-' + role + '-' + str(index) + '.png')))
        needle = {'ksgs': 'DEMO-BTS-LIVE', 'bgd': 'DEMO 03', 'infra': 'DEMO-RENEWAL-PRACTICE'}[role]
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "//tr[contains(@class,'o_data_row')][contains(.,'" + needle + "')]"))).click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.o_form_view')))
        if role == 'ksgs':
            wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(.,'Hồ sơ hợp đồng')]"))).click()
        wait.until(lambda d: needle in d.find_element(By.TAG_NAME, 'body').text or role in ('ksgs', 'infra'))
        assert not driver.find_elements(By.CSS_SELECTOR, '.o_error_dialog'), driver.find_element(By.TAG_NAME, 'body').text
        driver.save_screenshot(str(folder / ('ui-' + role + '.png')))
        report.append({'role': role, 'url': driver.current_url,
                       'visible_text': driver.find_element(By.TAG_NAME, 'body').text[:3500]})
    driver.get('http://127.0.0.1:8025')
    WebDriverWait(driver, 30).until(lambda d: 'Mailpit' in d.title)
    driver.save_screenshot(str(folder / 'ui-mailpit.png'))
    report.append({'service': 'Mailpit', 'title': driver.title})
finally:
    driver.save_screenshot(str(folder / 'ui-last.png'))
    (folder / 'browser-last.txt').write_text(driver.current_url + '\n' + driver.find_element(By.TAG_NAME, 'body').text,
                                            encoding='utf-8')
    driver.quit()
    (folder / 'browser-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True, indent=2))
