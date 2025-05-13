
import argparse
from utils.db import load_reference_from_csv

def main():
    parser = argparse.ArgumentParser(description='Carregar referência de alunos no DB')    
    parser.add_argument('--file', required=True, help='CSV com colunas re,nome,pelotao')
    args = parser.parse_args()
    load_reference_from_csv(args.file)    
    print("Referência carregada")

if __name__ == '__main__':
    main()