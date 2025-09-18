import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://treinamento.emergencia.sesdec.ro.gov.br/sade/sade/public/index.php/login"
LOGIN_URL = BASE_URL

DB_DIR = os.path.join(BASE_DIR, os.pardir, "dbs")
DB_PATH = os.path.join(DB_DIR, "database.sqlite")

USERNAME = os.getenv("PMRO_USER", "vm_100091951")
PASSWORD = os.getenv("PMRO_PASS", "dinfo2025")

DEFAULT_TIMEOUT = 60

