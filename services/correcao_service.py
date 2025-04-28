from models.resultado import Resultado
from services.coleta_service import *
from utils.helpers import tratar_mensagem_erro
import unicodedata

combinacoes_avaliadas = set()

def normalize_str(s: str) -> str:   
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.strip().casefold()

def corrigir_a(driver, tarefa, dados, erros_coleta):
    erros_avaliacao = []
    nota = 0

    
    re_valor    = tarefa.re
    nome_tabela = tarefa.nome
    protocolo   = tarefa.protocolo
   
    if not dados.get("nome_geracao", ""):
        erros_avaliacao.append(
            tratar_mensagem_erro(
                "Nome do aluno que gerou a ocorrência no SISEG "
                "é diferente do nome do aluno"
            )
        )
        status = "erro"
    else:
        status = "ok"

    
    if status == "ok":       
        if nome_tabela.strip().lower() == dados["nome_geracao"].strip().lower():
            codigo = dados.get("codigo_fechamento", "").strip()            
            if codigo == "Averiguação Policial sem Alteração":                
                tipos = dados.get("tipo_envolvimento", [])
                if isinstance(tipos, str):
                    tipos = [tipos]
                tipos_norm = [t.strip().lower() for t in tipos if t.strip()]

                if "abordado" in tipos_norm:
                    origem = dados.get("origem_abertura_oc", "").strip().lower()
                    if origem != "mobile":
                        nota = 1
                        erros_avaliacao.clear()
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

def corrigir_b(driver, tarefa, dados, erros_coleta):  
    erros_avaliacao = []
    nota = 0    
    re_valor    = tarefa.re
    nome_tabela = tarefa.nome
    protocolo   = tarefa.protocolo    
    
    if not dados.get("nome_geracao", ""):
        erros_avaliacao.append(
            tratar_mensagem_erro(
                "Nome do aluno que gerou a ocorrência no SISEG "
                "é diferente do nome do aluno"
            )
        )
        status = "erro"
    else:
        status = "ok"

    
    if status == "ok":        
        if nome_tabela.strip().lower() == dados["nome_geracao"].strip().lower():
            codigo = dados.get("codigo_fechamento", "").strip()            
            if codigo == "Resolvido no local":
                nota = 1
                erros_avaliacao.clear()
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
    
    return Resultado(
        atividade='B',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )


def corrigir_c(driver, tarefa, dados, erros_coleta):    
    erros_avaliacao = []
    nota = 0
   
    re_valor    = tarefa.re
    nome_tabela = tarefa.nome
    protocolo   = tarefa.protocolo    
    status = "ok"
    
    nome_gerador = dados.get("nome_geracao", "").strip()
    if not nome_gerador:
        erros_avaliacao.append(
            tratar_mensagem_erro(
                "Nome do aluno que gerou a ocorrência no SISEG é diferente do nome do aluno"
            )
        )
        status = "erro"
   
    if status == "ok":
        if nome_tabela.strip().lower() != nome_gerador.lower():
            erros_avaliacao.append(
                tratar_mensagem_erro(
                    "Nome do aluno diferente do gerador da OC"
                )
            )
            status = "erro"
   
    if status == "ok":
        raw_nat   = dados.get("natureza", "")
        lista_nat = [n.strip().lower() for n in raw_nat.split(";") if n.strip()]
        esperado  = "averiguação de pessoa em atitude suspeita"
        if len(lista_nat) != 1 or lista_nat[0] != esperado:
            erros_avaliacao.append(
                tratar_mensagem_erro(
                    "Natureza inválida para a questão"
                )
            )
            status = "erro"
    
    if status == "ok":
        cmd_str = dados.get("comandante_guarnicao", "").strip()
        if not cmd_str:
            erros_avaliacao.append(
                tratar_mensagem_erro(
                    "Comandante da guarnição não informado"
                )
            )
            status = "erro"
        else:
            cmds = [c.strip().lower() for c in cmd_str.split(";") if c.strip()]
            if nome_tabela.strip().lower() not in cmds:
                erros_avaliacao.append(
                    tratar_mensagem_erro(
                        "Comandante da guarnição não confere"
                    )
                )
                status = "erro"
    
    if status == "ok":
        te = dados.get("tipo_envolvimento", [])
        if isinstance(te, str):
            te = [te]
        te_norm = [
            s.strip().lower()
            for item in te
            for s in item.split(";")
            if s.strip()
        ]
        if "abordado" not in te_norm:
            erros_avaliacao.append(
                tratar_mensagem_erro(
                    "Nenhum tipo de envolvimento 'abordado'"
                )
            )
            status = "erro"
    
    if status == "ok":
        ori = dados.get("origem_abertura_oc", "").strip().lower()
        if ori == "mobile":
            erros_avaliacao.append(
                tratar_mensagem_erro(
                    "Origem da abertura OC é 'mobile', deve ser via SISEG"
                )
            )
            status = "erro"
    
    if status == "ok":
        nota = 1
        erros_avaliacao.clear()         

   
    return Resultado(
        atividade='C',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )


def corrigir_d(driver, tarefa, dados, erros_coleta):
    erros_avaliacao = []
    nota = 0

    re_valor    = tarefa.re
    nome_tabela = tarefa.nome.strip().lower()
    protocolo   = tarefa.protocolo

    nome_gerador = dados.get("nome_geracao", "").strip()
    if not nome_gerador:
        erros_avaliacao.append(tratar_mensagem_erro(
            "Nome do aluno que gerou a ocorrência no SISEG é diferente do nome do aluno"
        ))
    else:
        if nome_tabela != nome_gerador.lower():
            erros_avaliacao.append(tratar_mensagem_erro(
                "Nome do aluno diferente do gerador da OC"
            ))   
    
    if not erros_avaliacao:           
        required_naturezas = ["posse irregular de arma de fogo de uso permitido", "lesão corporal leve - dolosa"] 
        natureza_texto = dados.get("natureza", "").lower()
        missing = [req for req in required_naturezas if req not in natureza_texto]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != nome_tabela:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
            ))

    if not erros_avaliacao:        
        te = dados.get("tipo_envolvimento", [])
        if isinstance(te, str):
            te = [te]
        te_norm = [
            normalize_str(p)
            for item in te
            for p in item.split(";")
            if p.strip()
        ]
        for obrigatório in ("abordado", "vitima", "autor"):
            if obrigatório not in te_norm:
                erros_avaliacao.append(tratar_mensagem_erro(
                    f"Nenhum dos envolvidos possui o tipo de envolvimento '{obrigatório}'"
                ))
    
    if not erros_avaliacao:   
        origem = normalize_str(dados.get("origem_abertura_oc", ""))
        if origem == "mobile":
            erros_avaliacao.append(tratar_mensagem_erro(
                "Origem da abertura OC é 'mobile'; a ocorrência deve ser iniciada via SISEG"
            ))

    if not erros_avaliacao:        
        relato_norm = normalize_str(dados.get("relato_policial", ""))
        relato_norm = " ".join(relato_norm.split())        
        frase_norm = normalize_str(
            "comunica-se à autoridade judiciária competente"
        )        
        if frase_norm not in relato_norm:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Relato policial não contém o critério padrão de confecção por IA"
            ))

    if not erros_avaliacao:        
        arma_list = [
            normalize_str(p)
            for p in dados.get("tipo_armas", "").split(";")
            if p.strip()
        ]
        if "tipo arma de fogo" not in arma_list:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui arma de fogo cadastrada"
            ))

    if not erros_avaliacao:        
        obj_list = [
            normalize_str(p)
            for p in dados.get("tipo_situacao", "").split(";")
            if p.strip()
        ]
        if "faca/utensilio de cozinha" not in obj_list:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Faca/Utensílio de cozinha cadastrada"
            ))
    
    if not erros_avaliacao:
        nota = 1
    
    return Resultado(
        atividade='D',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )

def corrigir_e(driver, tarefa, dados, erros_coleta):
    erros_avaliacao = []
    nota = 0

    re_valor    = tarefa.re
    nome_tabela = tarefa.nome.strip().lower()
    protocolo   = tarefa.protocolo

    if not erros_avaliacao:           
        required_cf = ["termo circunstanciado"] 
        cf = dados.get("codigo_fechamento", "").lower()
        missing = [req for req in required_cf if req not in cf]
        if missing:
            msg = f"Código de fechamento divergente do solicitado - termo circunstanciado : {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg)) 

    if not erros_avaliacao:           
        required_naturezas = ["perturbação do trabalho ou sossego alheios", "desacato"] 
        natureza_texto = dados.get("natureza", "").lower()
        missing = [req for req in required_naturezas if req not in natureza_texto]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != nome_tabela:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
            ))

    if not erros_avaliacao:           
        required_envolvidos = ["fiel depositário"] 
        envolvimento = dados.get("tipo_envolvimento", "").lower()
        missing = [req for req in required_envolvidos if req not in envolvimento]
        if missing:
            msg = f"Nenhum dos envolvidos possui o tipo de envolvimento solicitado {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))   

    if not erros_avaliacao:       
        obj_list = [
            normalize_str(p)
            for p in re.split(r"[;,]", dados.get("tipo_situacao", ""))
            if p.strip()
        ]        
        if "apreendido por infracao penal" not in obj_list:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui 'Apreendido por infração penal' cadastrada"
            ))
        if "deposito fiel" not in obj_list:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui 'Depósito fiel' cadastrada"
            ))      


    if not erros_avaliacao:
        nota = 1
    
    return Resultado(
        atividade='E',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )

def corrigir_f(driver, tarefa, dados, erros_coleta):
    erros_avaliacao = []
    nota = 0

    re_valor    = tarefa.re
    nome_tabela = tarefa.nome.strip().lower()
    protocolo   = tarefa.protocolo

    if not erros_avaliacao:           
        required_cf = ["termo circunstanciado"] 
        cf = dados.get("codigo_fechamento", "").lower()
        missing = [req for req in required_cf if req not in cf]
        if missing:
            msg = f"Código de fechamento divergente do solicitado - termo circunstanciado : {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg)) 

    if not erros_avaliacao:           
        required_naturezas = ["lesão corporal culposa em sinistro de trânsito", "posse ou porte de drogas para uso pessoal", "sinistro de trânsito (com pessoa ferida ou morta)"] 
        natureza_texto = dados.get("natureza", "").lower()
        missing = [req for req in required_naturezas if req not in natureza_texto]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != nome_tabela:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
            ))

    if not erros_avaliacao:           
        required_envolvidos = ["fiel depositário"] 
        envolvimento = dados.get("tipo_envolvimento", "").lower()
        missing = [req for req in required_envolvidos if req not in envolvimento]
        if missing:
            msg = f"Nenhum dos envolvidos possui o tipo de envolvimento solicitado {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))   
                
    if not erros_avaliacao:        
        relato_norm = normalize_str(dados.get("relato_policial", ""))
        relato_norm = " ".join(relato_norm.split())        
        frase_norm = normalize_str(
            "comunica-se à autoridade judiciária competente"
        )        
        if frase_norm not in relato_norm:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Relato policial não contém o critério padrão de confecção por IA"
            ))
        
    if not erros_avaliacao:
        nota = 1
    
    return Resultado(
        atividade='F',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )