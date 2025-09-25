import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# BASE_URL = "https://emergencia.sesdec.ro.gov.br/sade/sade/public/index.php/login"
BASE_URL = "https://treinamento.emergencia.sesdec.ro.gov.br/sade/sade/public/index.php/login"
LOGIN_URL = BASE_URL


USERNAME = os.getenv("PMRO_USER", "vm_100091951")
PASSWORD = os.getenv("PMRO_PASS", "")

# USERNAME = os.getenv("PMRO_USER", "100091951_administrador_sistema")
# PASSWORD = os.getenv("PMRO_PASS", "")

DEFAULT_TIMEOUT = 60

