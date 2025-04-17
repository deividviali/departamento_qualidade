#settings

import os

# Base da aplicação
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# URLs do SISEG
BASE_URL = "https://treinamento.emergencia.sesdec.ro.gov.br/sade/sade/public/"
LOGIN_URL = BASE_URL + "login"

# Diretório de bancos de dados por atividade
# Usa pasta 'dbs' no nível acima de 'config/'
DB_DIR = os.path.join(BASE_DIR, os.pardir, "dbs")
DB_PATH_TEMPLATE = os.path.join(DB_DIR, "database_{atividade}.db")

# Credenciais para login no SISEG (via variáveis de ambiente)
USERNAME = os.getenv("PMRO_USER", "100091951_administrador")
PASSWORD = os.getenv("PMRO_PASS", "brune864311")

# Timeout padrão para espera de elementos (em segundos)
DEFAULT_TIMEOUT = 30