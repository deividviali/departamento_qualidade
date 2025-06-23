#tarefa

from typing import List

class Tarefa:
    def __init__(
        self,
        protocolo: str,
        re: str,
        nome: str,
        pelotao: str,
        atividades: List[str],
        curso: str = ""
    ):
        self.protocolo = protocolo
        self.re = re
        self.nome = nome
        self.pelotao = pelotao
        self.atividades = atividades
        self.curso = curso
