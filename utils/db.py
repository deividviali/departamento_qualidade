import os
import sqlite3
import csv
from config.settings import DB_DIR, DB_PATH_TEMPLATE


def get_connection(atividade: str):
    os.makedirs(DB_DIR, exist_ok=True)
    path = DB_PATH_TEMPLATE.format(atividade=atividade.lower())
    return sqlite3.connect(path)


def init_db(atividade: str):
    conn = get_connection(atividade)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            re TEXT PRIMARY KEY,
            nome TEXT,
            pelotao TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            atividade TEXT,
            protocolo TEXT,
            re TEXT,
            nome TEXT,
            pelotao TEXT,
            data_oc TEXT,
            relato_policial TEXT,
            complemento_oc TEXT,
            nome_geracao TEXT,
            info_protocolo TEXT,
            status TEXT,
            nota REAL,
            codigo_fechamento TEXT,
            origem_abertura_oc TEXT,
            envolvido TEXT,
            tipo_envolvimento TEXT,
            comandante_guarnicao TEXT,
            objetos TEXT,
            tipo_situacao TEXT,
            veiculos TEXT,
            tipo_veiculos TEXT,
            armas TEXT,
            tipo_armas TEXT,
            drogas TEXT,
            tipo_drogas TEXT,
            natureza TEXT,
            erro_coleta_dados TEXT,
            erros_avaliacao TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (protocolo, re)
        )
    ''')
    conn.commit()
    return conn


def load_reference_from_csv(atividade: str, csv_path: str):
    conn = init_db(atividade)
    c = conn.cursor()    
    with open(csv_path, newline='', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter=';', skipinitialspace=True)
        for row in reader:
            c.execute(
                "INSERT OR REPLACE INTO students (re, nome, pelotao) VALUES (?, ?, ?)",
                (row['re'], row['nome'], row.get('pelotao', ''))
            )
    conn.commit()
    conn.close()


def get_student(atividade: str, re_val: str):
    conn = get_connection(atividade)
    c = conn.cursor()
    c.execute("SELECT nome, pelotao FROM students WHERE re = ?", (re_val,))
    row = c.fetchone()
    conn.close()
    return row


def save_result(atividade: str, resultado):
    conn = get_connection(atividade)
    c = conn.cursor()
    data = resultado.as_dict()
    c.execute('''
        INSERT OR REPLACE INTO results (
            atividade ,protocolo, re, nome, pelotao,
            data_oc, relato_policial, complemento_oc,
            nome_geracao, info_protocolo, status,
            nota, codigo_fechamento, origem_abertura_oc,
            envolvido, tipo_envolvimento, comandante_guarnicao,
            objetos, tipo_situacao, veiculos, tipo_veiculos,
            armas, tipo_armas, drogas, tipo_drogas,
            natureza, erro_coleta_dados, erros_avaliacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('atividade'), data.get('protocolo'), data.get('re'), data.get('nome'), data.get('pelotao'),
        data.get('data_oc'), data.get('relato_policial'), data.get('complemento_oc'),
        data.get('nome_geracao'), data.get('info_protocolo'), data.get('status'),
        data.get('nota'), data.get('codigo_fechamento'), data.get('origem_abertura_oc'),
        data.get('envolvido'), data.get('tipo_envolvimento'), data.get('comandante_guarnicao'),
        data.get('objetos'), data.get('tipo_situacao'), data.get('veiculos'),
        data.get('tipo_veiculos'), data.get('armas'), data.get('tipo_armas'),
        data.get('drogas'), data.get('tipo_drogas'), data.get('natureza'),
        data.get('erro_coleta_dados'), data.get('erros_avaliacao')
    ))
    conn.commit()
    conn.close()