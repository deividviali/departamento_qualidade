# services/login_service_producao_siseg.py
#função para windos

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium import webdriver
# from config.settings import LOGIN_URL, USERNAME, PASSWORD, DEFAULT_TIMEOUT
# import time, json

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
#         WebDriverWait(driver, DEFAULT_TIMEOUT).until(
#             EC.element_to_be_clickable((By.ID, "Selecionar"))
#         ).click()
#     except Exception as e:
#         print(f"[login_service] Aviso inesperado no 'Selecionar': {e}")

#     return True


# # Nova função para importar no Flask
# def login_siseg(headless=False): #True - para esconder
#     driver = iniciar_navegador(headless=headless)
#     sucesso = efetuar_login(driver)
#     if not sucesso:
#         driver.quit()
#         return None
#     return driver

    


# # Modo standalone (compatível com subprocess antigo)
# if __name__ == "__main__":
#     try:
#         result = login_siseg(headless=True)
#         print(json.dumps(result))
#     except Exception as e:
#         print(json.dumps({"erro": str(e)}))


     ###Funciona na VM
import os
import shutil
import subprocess
import tempfile
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from config.settings import LOGIN_URL, USERNAME_PRODUCAO, PASSWORD_PRODUCAO, DEFAULT_TIMEOUT


def find_free_display(start: int = 200) -> str:
    """Procura um display livre a partir do número indicado"""
    disp = start
    while os.path.exists(f"/tmp/.X11-unix/X{disp}"):
        disp += 1
    return f":{disp}"


def iniciar_navegador(headless: bool = False):
    # inicia Xvfb
    xvfb_bin = shutil.which("Xvfb") or "/usr/bin/Xvfb"
    display = find_free_display(200)
    xvfb_cmd = [xvfb_bin, display, "-screen", "0", "1920x1080x24"]
    xvfb_proc = subprocess.Popen(
        xvfb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    os.environ["DISPLAY"] = display
    print(f"[login_service] Xvfb iniciado no display {display}")

    # localiza binário do Chrome
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

    # cria perfil temporário para evitar conflito
    user_data_dir = tempfile.mkdtemp(prefix="siseg_profile_")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    driver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    service = ChromeService(executable_path=driver_path, log_path="/var/log/chromedriver.log")
    driver = webdriver.Chrome(service=service, options=options)
    driver.xvfb_proc = xvfb_proc

    driver.set_page_load_timeout(DEFAULT_TIMEOUT)
    driver.get(LOGIN_URL)
    return driver


def efetuar_login(driver) -> bool:
    try:
        driver.find_element(By.ID, "username").send_keys(USERNAME_PRODUCAO)
        driver.find_element(By.ID, "password").send_keys(PASSWORD_PRODUCAO)
        driver.find_element(By.ID, "entrar").click()
    except (NoSuchElementException, Exception) as e:
        print(f"[login_service] Aviso: falha ao submeter login: {e}")
        return False

    time.sleep(8)

    try:
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "Selecionar"))
        ).click()
    except TimeoutException:
        print("[login_service] Timeout aguardando botão 'Selecionar'")
        return False
    except Exception as e:
        print(f"[login_service] Erro inesperado no 'Selecionar': {e}")
        return False

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


def login_siseg(headless=False):
    driver = iniciar_navegador(headless=headless)
    sucesso = efetuar_login(driver)
    if not sucesso:
        fechar_navegador(driver)
        return None
    return driver


if __name__ == "__main__":
    try:
        result = login_siseg(headless=True)
        if result:
            print(json.dumps({"status": "ok"}))
        else:
            print(json.dumps({"erro": "falha ao logar"}))
    except Exception as e:
        print(json.dumps({"erro": str(e)}))
