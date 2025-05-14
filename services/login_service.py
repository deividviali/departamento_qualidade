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
#     time.sleep(8)
    
#     try:
#         WebDriverWait(driver, 110).until(EC.element_to_be_clickable((By.ID, "Selecionar"))).click()
#     except Exception as e:
#         print(f"[login_service] Aviso inesperado no 'Selecionar': {e}")

#     return True



     ###Funciona na VM
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
from config.settings import LOGIN_URL, DEFAULT_TIMEOUT, USERNAME, PASSWORD

def find_free_display(start: int = 200) -> str:    
    disp = start    
    while os.path.exists(f"/tmp/.X11-unix/X{disp}"):
        disp += 1
    return f":{disp}"

def iniciar_navegador(headless: bool = False):
    try:
        free_out = subprocess.check_output(['free', '-m']).decode()
    except Exception:
        free_out = 'Não foi possível obter stats de memória'
    print(f"[login_service] Memória disponível (MB):\n{free_out}")
    try:
        free_out = subprocess.check_output(['free', '-m']).decode()
    except Exception:
        free_out = 'Não foi possível obter stats de memória'
    print(f"[login_service] Memória disponível (MB):\n{free_out}")   
    
    xvfb_bin = shutil.which("Xvfb") or "/usr/bin/Xvfb"
    display = find_free_display(200)
    xvfb_cmd = [xvfb_bin, display, "-screen", "0", "1920x1080x24"]
    xvfb_proc = subprocess.Popen(
        xvfb_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )   
    os.environ["DISPLAY"] = display
    print(f"[login_service] Xvfb iniciado no display {display}")  

    chrome_binary = (
        shutil.which("google-chrome-stable")
        or shutil.which("google-chrome")
        or shutil.which("chromium-browser")
    )
    if not chrome_binary:
        raise RuntimeError("Binário do Chrome não encontrado")

    options = ChromeOptions()
    options.binary_location = chrome_binary
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")    
    
    driver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    service = ChromeService(executable_path=driver_path, log_path="/var/log/chromedriver.log")
    driver = webdriver.Chrome(service=service, options=options)
    print("[login_service] WebDriver Chrome instanciado com sucesso") 
    
    driver.xvfb_proc = xvfb_proc    
    driver.set_page_load_timeout(DEFAULT_TIMEOUT)
    driver.get(LOGIN_URL)
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
        print(f"[login_service] Erro ao fechar navegador: {e}")    
    if hasattr(driver, "xvfb_proc"):
        try:
            driver.xvfb_proc.terminate()
            driver.xvfb_proc.wait(timeout=5)
            print(f"[login_service] Xvfb no display {os.environ.get('DISPLAY')} finalizado")
        except Exception:
            print("[login_service] Não foi possível finalizar o Xvfb")