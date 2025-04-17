# services/login_service.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from config.settings import LOGIN_URL, USERNAME, PASSWORD, DEFAULT_TIMEOUT
import time

def iniciar_navegador(headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(LOGIN_URL)
    return driver

def efetuar_login(driver) -> bool:    
    try:
        # preenche credenciais
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "entrar").click()
    except (NoSuchElementException, Exception) as e:
        print(f"[login_service] Aviso: falha ao submeter login: {e}")
        return False
    time.sleep(5)
    
    try:
        WebDriverWait(driver, 110).until(EC.element_to_be_clickable((By.ID, "Selecionar"))).click()
    except Exception as e:
        print(f"[login_service] Aviso inesperado no 'Selecionar': {e}")

    return True





    time.sleep(5)