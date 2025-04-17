# services/export_service.py

from models.resultado import Resultado
from utils.db import save_result
from utils.helpers import tratar_mensagem_erro


def _print_single(resultado: Resultado):
    """
    Imprime no console um único Resultado.
    """
    print("\n=== Resultado da Tarefa ===")
    print(f"Protocolo: {resultado.protocolo}")
    print(f"RE: {resultado.re}")
    print(f"Nome: {resultado.nome}")
    print(f"Pelotão: {resultado.pelotao}\n")

    print("-- Dados Coletados --")
    for campo, valor in resultado.dados.items():
        print(f"  {campo}: {valor}")
    print(f"\nNota: {resultado.nota}\n")

    if resultado.erros_coleta:
        print("Erros de Coleta:")
        for err in resultado.erros_coleta:
            print(f"  - {err}")

    if resultado.erros_avaliacao:
        print("Erros de Avaliação:")
        for err in resultado.erros_avaliacao:
            print(f"  - {err}")


def print_console(resultados):
    """
    Imprime no console um ou vários Resultados.
    Aceita tanto um único Resultado quanto uma lista de Resultados.
    """
    if isinstance(resultados, list):
        for res in resultados:
            _print_single(res)
    else:
        _print_single(resultados)


def export_to_db(resultado: Resultado):
    """
    Persiste o Resultado no banco de dados.
    """
    save_result(resultado.tarefa_atividade, resultado)
