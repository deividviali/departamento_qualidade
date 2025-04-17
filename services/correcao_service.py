from models.resultado import Resultado
from services.coleta_service import *
from utils.helpers import tratar_mensagem_erro

combinacoes_avaliadas = set()

def corrigir_a(driver, tarefa, dados, erros_coleta):
    erros_coleta = []
    erros_avaliacao = []
    nota = 0
    dados = {}

    # 1) Coleta de dados
    for tipo in tarefa.atividades:
        func = globals().get(f"coletar_{tipo.lower()}")
        if func:
            try:
                dados[tipo] = func(driver, tarefa.protocolo, erros_coleta)
            except Exception as e:
                erros_coleta.append(tratar_mensagem_erro(str(e)))
        else:
            erros_avaliacao.append(
                f"Função coletar_{tipo.lower()} não encontrada"
            )

    # 1.5) Achatar o dicionário de dados
    flat = {}
    for info in dados.values():
        flat.update(info)
    dados = flat

    # 2) Início da etapa de avaliação
    re_valor    = tarefa.re
    nome_tabela = tarefa.nome
    protocolo   = tarefa.protocolo

    if dados.get("nome_geracao", ""):
        status = "ok"
    else:
        status = "protocolo não encontrado"
        erros_avaliacao.append(
            tratar_mensagem_erro(
                "Nome do aluno que gerou a ocorrência no SISEG "
                "é diferente do nome do aluno"
            )
        )

    if status.lower() == "ok":
        # comparo nomes
        if nome_tabela.strip().lower() == dados["nome_geracao"].strip().lower():
            codigo = dados.get("codigo_fechamento", "").strip()
            validos = [
                "Averiguação Policial sem Alteração",
                "Resolvido no local"
            ]
            if codigo in validos:
                chave = (re_valor, codigo)
                if chave in combinacoes_avaliadas:
                    msg = f"Combinação {chave} já avaliada anteriormente."
                    erros_avaliacao.append(tratar_mensagem_erro(msg))
                else:
                    if codigo.lower() == "resolvido no local":
                        nota = 1
                        combinacoes_avaliadas.add(chave)
                    else:
                        # regras de tipo_envolvimento e origem
                        tipos = dados.get("tipo_envolvimento", [])
                        if isinstance(tipos, str):
                            tipos = [tipos]
                        tipos_norm = [
                            t.strip().lower() for t in tipos if t.strip()
                        ]
                        if "abordado" in tipos_norm:
                            origem = dados.get(
                                "origem_abertura_oc", ""
                            ).strip().lower()
                            if origem != "mobile":
                                nota = 1
                                combinacoes_avaliadas.add(chave)
                            else:
                                erros_avaliacao.append(
                                    tratar_mensagem_erro(
                                        "Origem é 'mobile'; deve ser via SISEG"
                                    )
                                )
                        else:
                            erros_avaliacao.append(
                                tratar_mensagem_erro(
                                    "Nenhum tipo de envolvimento 'abordado'"
                                )
                            )
            else:
                erros_avaliacao.append(
                    tratar_mensagem_erro(
                        "Código de fechamento inválido para a questão"
                    )
                )
        else:
            erros_avaliacao.append(
                tratar_mensagem_erro(
                    "Nome do aluno diferente do nome de geração da OC"
                )
            )

    # 3) Retorno
    return Resultado(
        atividade='A',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )
