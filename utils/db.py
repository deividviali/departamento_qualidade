
# from models.resultado import Resultado
# import os
# from sqlalchemy import create_engine
# from sqlalchemy import text



# def init_db():    
#     pass

# def get_db_connection():
#     DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
#     DB_USER = os.getenv("DB_USER", "root")
#     DB_PASS = os.getenv("DB_PASS", "")
#     DB_NAME = os.getenv("DB_NAME", "suporte_ti_DINFO")
#     DB_PORT = os.getenv("DB_PORT", "3306")

#     engine = create_engine(
#         f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
#         echo=False,
#         pool_pre_ping=True,
#         future=True
#     )
#     return engine


# def get_student(re_val: str):
#     conn = get_db_connection()
#     c = conn.cursor()
#     c.execute("SELECT nome, pelotao, curso FROM students WHERE re = %s", (re_val,))
#     row = c.fetchone()
#     conn.close()
#     return row



# def save_result(atividade: str, resultado: Resultado):
#     engine = get_db_connection()
#     data = resultado.as_dict()
#     data['atividade'] = atividade

#     sql = text('''
#         REPLACE INTO results (
#             atividade, protocolo, re, nome, pelotao, curso,
#             data_oc, relato_policial, complemento_oc,
#             nome_geracao, info_protocolo, status,
#             nota, codigo_fechamento, origem_abertura_oc,
#             envolvido, tipo_envolvimento, comandante_guarnicao,
#             objetos, tipo_situacao, veiculos, tipo_veiculos,
#             armas, tipo_armas, drogas, tipo_drogas,
#             natureza, erro_coleta_dados, erros_avaliacao
#         ) VALUES (
#             :atividade, :protocolo, :re, :nome, :pelotao, :curso,
#             :data_oc, :relato_policial, :complemento_oc,
#             :nome_geracao, :info_protocolo, :status,
#             :nota, :codigo_fechamento, :origem_abertura_oc,
#             :envolvido, :tipo_envolvimento, :comandante_guarnicao,
#             :objetos, :tipo_situacao, :veiculos, :tipo_veiculos,
#             :armas, :tipo_armas, :drogas, :tipo_drogas,
#             :natureza, :erro_coleta_dados, :erros_avaliacao
#         )
#     ''')

#     with engine.begin() as conn:
#         conn.execute(sql, data)


## Teste - caso funcione tem que ajustar o código da aplicação
import os
from sqlalchemy import create_engine, text
from models.resultado import Resultado

import os
from sqlalchemy import create_engine, text
from models.resultado import Resultado

# Configurações Banco Principal
DB_HOST_MAIN = os.getenv("DB_HOST", "127.0.0.1")
DB_USER_MAIN = os.getenv("DB_USER", "root")
DB_PASS_MAIN = os.getenv("DB_PASS", "")
DB_NAME_MAIN = os.getenv("DB_NAME_MAIN", "suporte_ti_DINFO") #verificar qual nome do banco correto
DB_NAME_MAIN = os.getenv("DB_NAME_MAIN", "suporte_ti_dinfo")
DB_PORT_MAIN = os.getenv("DB_PORT", "3306")


# Configuração Banco Externo (SIGA)
DB_HOST_EXT = "172.16.139.20"
DB_PORT_EXT = 33061
DB_USER_EXT = "app.suporte.dinfo"
DB_PASS_EXT = "5hjnk4Ji&z%&"
DB_NAME_EXT = "siga-homo83"  

# Criar engines
engine_main = create_engine(
    f"mysql+pymysql://{DB_USER_MAIN}:{DB_PASS_MAIN}@{DB_HOST_MAIN}:{DB_PORT_MAIN}/{DB_NAME_MAIN}",
    echo=False,
    pool_pre_ping=True,
    future=True
)

engine_extern = create_engine(
    f"mysql+pymysql://{DB_USER_EXT}:{DB_PASS_EXT}@{DB_HOST_EXT}:{DB_PORT_EXT}/{DB_NAME_EXT}",
    echo=False,
    pool_pre_ping=True,
    future=True
)

# Funções de acesso
def get_engine_extern():
    return engine_extern

def get_db_connection(main=True):
    """Retorna engine do banco principal (main=True) ou externo (main=False)."""
    return engine_main if main else engine_extern

def get_student(re_val: str):
    engine = get_db_connection(main=True)  # usa banco principal
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT nome, pelotao, curso FROM students WHERE re = :re"),
            {"re": re_val}
        ).fetchone()
    return row

def save_result(atividade: str, resultado: Resultado):
    engine = get_db_connection(main=True)  # sempre no principal
    data = resultado.as_dict()
    data['atividade'] = atividade

    sql = text('''
        REPLACE INTO results (
            atividade, protocolo, re, nome, pelotao, curso,
            data_oc, relato_policial, complemento_oc,
            nome_geracao, info_protocolo, status,
            nota, codigo_fechamento, origem_abertura_oc,
            envolvido, tipo_envolvimento, comandante_guarnicao,
            objetos, tipo_situacao, veiculos, tipo_veiculos,
            armas, tipo_armas, drogas, tipo_drogas,
            natureza, erro_coleta_dados, erros_avaliacao
        ) VALUES (
            :atividade, :protocolo, :re, :nome, :pelotao, :curso,
            :data_oc, :relato_policial, :complemento_oc,
            :nome_geracao, :info_protocolo, :status,
            :nota, :codigo_fechamento, :origem_abertura_oc,
            :envolvido, :tipo_envolvimento, :comandante_guarnicao,
            :objetos, :tipo_situacao, :veiculos, :tipo_veiculos,
            :armas, :tipo_armas, :drogas, :tipo_drogas,
            :natureza, :erro_coleta_dados, :erros_avaliacao
        )
    ''')

    with engine.begin() as conn:
        conn.execute(sql, data)
