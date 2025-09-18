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
        erros_avaliacao: List[str],
        curso: str = ""
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
        self.curso = curso
        

    def as_dict(self):
        base = {
            'atividade': self.atividade,
            'protocolo': self.protocolo,
            're': self.re,
            'nome': self.nome,
            'pelotao': self.pelotao,
            'curso': self.curso,
        }

        base.update({
            'nota': self.nota,
            'status': 'certo' if self.nota == 1 else 'errado',
            'erro_coleta_dados': '; '.join(self.erros_coleta),
            'erros_avaliacao': '; '.join(self.erros_avaliacao),
            'objetos': self.dados.get('objetos', ''),
            'tipo_situacao': self.dados.get('tipo_situacao', ''),
            'veiculos': self.dados.get('veiculos', ''),
            'tipo_veiculos': self.dados.get('tipo_veiculos', ''),
            'armas': self.dados.get('armas', ''),
            'tipo_armas': self.dados.get('tipo_armas', ''),
            'drogas': self.dados.get('drogas', ''),
            'tipo_drogas': self.dados.get('tipo_drogas', ''),
            'natureza': self.dados.get('natureza', ''),
            'data_oc': self.dados.get('data_oc', ''),
            'relato_policial': self.dados.get('relato_policial', ''),
            'complemento_oc': self.dados.get('complemento_oc', ''),
            'nome_geracao': self.dados.get('nome_geracao', ''),
            'info_protocolo': self.dados.get('info_protocolo', ''),
            'codigo_fechamento': self.dados.get('codigo_fechamento', ''),
            'origem_abertura_oc': self.dados.get('origem_abertura_oc', ''),
            'envolvido': self.dados.get('envolvido', ''),
            'tipo_envolvimento': self.dados.get('tipo_envolvimento', ''),
            'comandante_guarnicao': self.dados.get('comandante_guarnicao', ''),
        })

        return base
