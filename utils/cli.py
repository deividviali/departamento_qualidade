import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Automação de correção por atividade')
    parser.add_argument('--atividade', required=True,
                        choices=['A','B','C','D'], help='Identificador da atividade')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--re', help='Registro Estatístico')
    group.add_argument('--batch-file', help='CSV com colunas re e protocolo')
    parser.add_argument('--protocolo', help='Número do protocolo (necessário com --re)')
    return parser.parse_args()