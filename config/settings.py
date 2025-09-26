import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL_PRODUCAO = "https://emergencia.sesdec.ro.gov.br/sade/sade/public/index.php/login"
LOGIN_URL_PRODUCAO = BASE_URL_PRODUCAO

USERNAME_PRODUCAO = os.getenv("PMRO_USER_PRODUCAO", "vm_100091951")
PASSWORD_PRODUCAO = os.getenv("PMRO_PASS_PRODUCAO", "")


BASE_URL = "https://treinamento.emergencia.sesdec.ro.gov.br/sade/sade/public/index.php/login"
LOGIN_URL = BASE_URL

USERNAME = os.getenv("PMRO_USER", "vm_100091951")
PASSWORD = os.getenv("PMRO_PASS", "")


DEFAULT_TIMEOUT = 60

