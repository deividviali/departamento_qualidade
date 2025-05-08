# services/login_service.py

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium import webdriver
# from config.settings import LOGIN_URL, USERNAME, PASSWORD, DEFAULT_TIMEOUT
# import time

# def iniciar_navegador(headless=False):
#     options = webdriver.ChromeOptions()
#     if headless:
#         options.add_argument("--headless")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--disable-dev-shm-usage")

#     driver = webdriver.Chrome(options=options)
#     driver.get(LOGIN_URL)
#     return driver

# def efetuar_login(driver) -> bool:    
#     try:
#         # preenche credenciais
#         driver.find_element(By.ID, "username").send_keys(USERNAME)
#         driver.find_element(By.ID, "password").send_keys(PASSWORD)
#         driver.find_element(By.ID, "entrar").click()
#     except (NoSuchElementException, Exception) as e:
#         print(f"[login_service] Aviso: falha ao submeter login: {e}")
#         return False
#     time.sleep(5)
    
#     try:
#         WebDriverWait(driver, 110).until(EC.element_to_be_clickable((By.ID, "Selecionar"))).click()
#     except Exception as e:
#         print(f"[login_service] Aviso inesperado no 'Selecionar': {e}")

#     return True



#Funciona na VM
import os
import time
import shutil
import subprocess
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from config.settings import LOGIN_URL, USERNAME, PASSWORD, DEFAULT_TIMEOUT

# Force unbuffered stdout for immediate logging
sys.stdout.reconfigure(line_buffering=True)

def iniciar_navegador(headless: bool = False):    
    try:
        free_out = subprocess.check_output(['free', '-m']).decode()
    except Exception:
        free_out = 'Não foi possível obter stats de memória'
    print(f"[login_service] Memória disponível (MB):\n{free_out}")
    
    chrome_binary = shutil.which("google-chrome-stable") or shutil.which("google-chrome") or shutil.which("chromium-browser")
    print(f"[login_service] chrome_binary = {chrome_binary}")
    if not chrome_binary or not os.path.exists(chrome_binary):
        raise RuntimeError(f"Binário do Chrome não encontrado: {chrome_binary}")
    
    options = ChromeOptions()
    options.binary_location = chrome_binary
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.accept_insecure_certs = True    
    options.page_load_strategy = 'eager'
   
    driver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    log_file = "/var/log/chromedriver.log"
    print(f"[login_service] Usando chromedriver em {driver_path}")
    print(f"[login_service] Logs do chromedriver em {log_file}")

    service = ChromeService(
        executable_path=driver_path,
        log_path=log_file,
    )
   
    try:
        print("[login_service] Instanciando Chrome WebDriver via Xvfb...")
        driver = webdriver.Chrome(service=service, options=options)
        print("[login_service] WebDriver Chrome instanciado com sucesso")
    except WebDriverException as e:
        print(f"[login_service] Erro na instanciação do WebDriver Chrome: {e}")
        raise
    
    driver.set_page_load_timeout(DEFAULT_TIMEOUT)
   
    try:
        print(f"[login_service] Navegando para {LOGIN_URL}...")
        driver.get(LOGIN_URL)
        print("[login_service] Página de login carregada")
    except TimeoutException:
        print("[login_service] Timeout carregando a página de login")
        raise
    except WebDriverException as e:
        print(f"[login_service] Erro ao navegar para login: {e}")
        raise

    return driver


def efetuar_login(driver) -> bool:
    print("[login_service] Step 1: Iniciando fluxo de login...")
    print(f"[DEBUG] URL atual: {driver.current_url}", flush=True)
    print(f"[DEBUG] Título da página: {driver.title}", flush=True)
    try:
        print("[login_service] Step 2: Preenchendo username")
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        print("[login_service] Username preenchido")

        print("[login_service] Step 3: Preenchendo password")
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        print("[login_service] Password preenchido")

        print("[login_service] Step 4: Clicando em 'entrar'")
        driver.find_element(By.ID, "entrar").click()
        print("[login_service] Clicou em 'entrar'")
    except (NoSuchElementException, Exception) as e:
        print(f"[login_service] Falha ao submeter login: {e}")
        return False

    try:
        print("[login_service] Step 5: Aguardando 'Selecionar'")
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "Selecionar"))
        )
        print("[login_service] 'Selecionar' disponível, clicando")
        driver.find_element(By.ID, "Selecionar").click()
        print("[login_service] Clicou em 'Selecionar'")
    except TimeoutException:
        print("[login_service] Timeout aguardando 'Selecionar'")
        return False
    except Exception as e:
        print(f"[login_service] Erro inesperado no 'Selecionar': {e}")
        return False

    print("[login_service] Step 6: Login efetuado com sucesso")
    print(f"[DEBUG] URL atual: {driver.current_url}", flush=True)
    print(f"[DEBUG] Título da página: {driver.title}", flush=True)
    return True


def fechar_navegador(driver):
    try:
        driver.quit()
        print("[login_service] Navegador fechado")
    except Exception as e:
        print(f"[login_service] Erro ao fechar navegador: {e}")


    