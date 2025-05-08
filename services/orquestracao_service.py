# services/orquestracao_service.py

from typing import List
from services.coleta_service import *  
from services.correcao_service import *  
from models.resultado import Resultado
from utils.helpers import tratar_mensagem_erro
import logging


COLLECTORS = {
    'A': coletar_a,
    'B': coletar_b,
    'C': coletar_c,
    'D': coletar_d,
    'E': coletar_e,
    'F': coletar_f,
    'PPE': coletar_ppe,
    
}
CORRECTORS = {
    'A': corrigir_a,
    'B': corrigir_b,
    'C': corrigir_c,
    'D': corrigir_d,
    'E': corrigir_e,
    'F': corrigir_f,
    'PPE': corrigir_ppe,
    
}

def orquestrar_tarefas(driver, tarefa) -> List[Resultado]:
    logging.debug(f"Orquestrando para RE={tarefa.re}, atividades={tarefa.atividades!r}")
    resultados: List[Resultado] = []

    for tipo in tarefa.atividades:
        tipo_up = tipo.upper()
        erros_coleta = []
        logging.debug(f"– Processando tipo {tipo_up!r}")
        
        collect = COLLECTORS.get(tipo_up)
        if not collect:
            raise ValueError(f"Coletor não encontrado para tipo {tipo_up}")
        logging.debug(f"  Usando coletor: {collect.__name__}")
        dados = collect(driver, tarefa.protocolo, erros_coleta)        
        correct = CORRECTORS.get(tipo_up)
        if not correct:
            raise ValueError(f"Corretor não encontrado para tipo {tipo_up}")
        logging.debug(f"  Usando corretor: {correct.__name__}")        
        resultado = correct(driver, tarefa, dados, erros_coleta)
        resultados.append(resultado)

    return resultados
