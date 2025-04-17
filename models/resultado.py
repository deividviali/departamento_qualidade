#resultado

from typing import Dict, List

class Resultado:
    def __init__(
        self,
        atividade: str,
        protocolo: str,
        re: str,
        nome: str,
        pelotao: str,
        dados: Dict[str, str],
        nota: int,
        erros_coleta: List[str],
        erros_avaliacao: List[str]
    ):
        self.atividade = atividade
        self.protocolo = protocolo
        self.re = re
        self.nome = nome
        self.pelotao = pelotao
        self.dados = dados
        self.nota = nota
        self.erros_coleta = erros_coleta
        self.erros_avaliacao = erros_avaliacao

    def as_dict(self):
        base = {
            'atividade': self.atividade,
            'protocolo': self.protocolo,
            're': self.re,
            'nome': self.nome,
            'pelotao': self.pelotao,
        }
        base.update(self.dados)
        base.update({
            'nota': self.nota,
            'erros_coleta': '; '.join(self.erros_coleta),
            'erros_avaliacao': '; '.join(self.erros_avaliacao)
        })
        return base