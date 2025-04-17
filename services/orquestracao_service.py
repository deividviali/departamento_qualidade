# services/orquestracao_service.py

from typing import List
from services.coleta_service import *  # importa coletar_a, coletar_b, etc.
from services.correcao_service import *  # importa corrigir_a, corrigir_b, etc.
from models.resultado import Resultado
from utils.helpers import tratar_mensagem_erro

# Mapeamento entre tipo de atividade e suas funções de coleta e correção
COLLECTORS = {
    'A': coletar_a,
    # 'B': coletar_b,
    # adicione mais conforme necessário
}
CORRECTORS = {
    'A': corrigir_a,
    # 'B': corrigir_b,
    # adicione mais conforme necessário
}

def orquestrar_tarefas(driver, tarefa) -> List[Resultado]:
    resultados: List[Resultado] = []

    for tipo in tarefa.atividades:
        tipo_up = tipo.upper()
        erros_coleta = []

        # 1) coleta
        collect = COLLECTORS.get(tipo_up)
        if not collect:
            raise ValueError(f"Coletor não encontrado para tipo {tipo_up}")
        dados = collect(driver, tarefa.protocolo, erros_coleta)

        # 2) avaliação
        correct = CORRECTORS.get(tipo_up)
        if not correct:
            raise ValueError(f"Corretor não encontrado para tipo {tipo_up}")
        
        # cada função corrigir_X deve ter assinatura: (driver, tarefa, dados, erros_coleta) -> Resultado
        resultado = correct(driver, tarefa, dados, erros_coleta)
        resultados.append(resultado)

    return resultados
