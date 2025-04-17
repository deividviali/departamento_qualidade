
# scripts/run_activity.py
import csv
import sys
from utils.cli import parse_args
from utils.db import init_db, get_student, save_result
from services.login_service import iniciar_navegador, efetuar_login
from services.export_service import print_console
from services.orquestracao_service import orquestrar_tarefas


def load_batch(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [(row['re'], row['protocolo']) for row in reader]


def main():
    args = parse_args()
    # Inicializa o banco de dados para a atividade
    init_db(args.atividade)

    # Inicia navegador e faz login
    driver = iniciar_navegador()
    efetuar_login(driver)

    # Carrega o conjunto de entradas (RE, protocolo)
    if args.batch_file:
        entries = load_batch(args.batch_file)
    else:
        if not args.protocolo:
            print("ERRO: --protocolo obrigatório", file=sys.stderr)
            sys.exit(1)
        entries = [(args.re, args.protocolo)]

    resultados = []
    # Permite múltiplos tipos, separados por vírgula
    atividades = [t.strip() for t in args.atividade.split(',')]

    from models.tarefa import Tarefa
    for re_val, protocolo in entries:
        student = get_student(args.atividade, re_val)
        if not student:
            print(f"Aluno RE {re_val} não encontrado.")
            continue
        nome, pelotao = student

        # Cria o objeto Tarefa com lista de atividades
        tarefa = Tarefa(
            protocolo=protocolo,
            re=re_val,
            nome=nome,
            pelotao=pelotao,
            atividades=atividades
        )

        # Orquestra coleta e avaliação para cada tipo
        batch_results = orquestrar_tarefas(driver, tarefa)
        for resultado in batch_results:
            # Persiste cada resultado individualmente
            save_result(args.atividade, resultado)
            resultados.append(resultado)

    # Fecha o navegador
    driver.quit()

    # Exibe todos os resultados no console (função aceita lista)
    print_console(resultados)


if __name__ == '__main__':
    main()
