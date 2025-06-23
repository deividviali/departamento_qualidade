import sqlite3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import DB_PATH
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def listar_colunas(cursor, tabela):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [info[1] for info in cursor.fetchall()]
    print(f"[DEBUG] Colunas da tabela '{tabela}': {colunas}")
    return colunas

def coluna_existe(cursor, tabela, coluna):
    try:
        colunas = listar_colunas(cursor, tabela)
        return coluna in colunas
    except Exception as e:
        print(f"[ERRO] Falha ao listar colunas da tabela {tabela}: {e}")
        return False

def tentar_adicionar_coluna(cursor, tabela, coluna, tipo):
    if coluna_existe(cursor, tabela, coluna):
        print(f"[INFO] A coluna '{coluna}' já existe na tabela '{tabela}'.")
        return
    try:
        print(f"[INFO] Tentando adicionar coluna '{coluna}' na tabela '{tabela}'...")
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        print(f"[OK] Coluna '{coluna}' adicionada com sucesso na tabela '{tabela}'.")
    except sqlite3.OperationalError as e:
        print(f"[FALHA] Não foi possível adicionar a coluna '{coluna}' em '{tabela}': {e}")

# Execução principal
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Adiciona a coluna 'curso' nas tabelas students e results
tentar_adicionar_coluna(cursor, 'students', 'curso', 'TEXT')
tentar_adicionar_coluna(cursor, 'results', 'curso', 'TEXT')

conn.commit()
conn.close()