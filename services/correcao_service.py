from models.resultado import Resultado
from services.coleta_service import *
from utils.helpers import tratar_mensagem_erro
import unicodedata
import re

combinacoes_avaliadas = set()

def normalize(text):
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower().strip()

def normalize_str(s: str) -> str:   
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.strip().casefold()

def normalize_simples(s: str) -> str:
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode().strip().lower()

def tem_envolvimento_para_tipo(lista, nome_alvo, envolvimento_alvo, tipo_alvo):
    nome_alvo = normalize_simples(nome_alvo)
    envolvimento_alvo = normalize_simples(envolvimento_alvo)
    tipo_alvo = normalize_simples(tipo_alvo)

    for registro in lista:
        nome = normalize_simples(registro.get("nome", ""))
        envolvimento = normalize_simples(registro.get("envolvimento", ""))
        tipo = normalize_simples(registro.get("tipos", ""))

        if nome_alvo in nome and envolvimento == envolvimento_alvo and tipo_alvo in tipo:
            return True
    return False

def tem_envolvimento(dados, nome_alvo, envolvimento_alvo):
    nome_alvo = normalize_simples(nome_alvo)
    envolvimento_alvo = normalize_simples(envolvimento_alvo)

    for registro in dados:
        nome = normalize_simples(registro.get("nome", ""))
        envolvimento = normalize_simples(registro.get("envolvimento", ""))
        if nome_alvo in nome and envolvimento == envolvimento_alvo:
            return True
    return False



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
                tipos_norm = []
                for item in tipos:
                    if isinstance(item, dict):
                        envolvimento = item.get("envolvimento", "").strip().lower()
                        tipos_norm.append(envolvimento)
                    elif isinstance(item, str):
                        tipos_norm.append(item.strip().lower())               
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
        natureza_texto = dados.get("natureza", "")
        natureza_lista = [n.strip().lower() for n in natureza_texto.split(";") if n.strip()]        
        missing = [req for req in required_naturezas if req not in natureza_lista]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != normalize(nome_tabela):
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
        required_naturezas = [
                        "perturbação do trabalho ou sossego alheios", 
                        "desacato",
                        "dano"
        ] 
        natureza_texto = dados.get("natureza", "")
        natureza_lista = [n.strip().lower() for n in natureza_texto.split(";") if n.strip()]        
        missing = [req for req in required_naturezas if req not in natureza_lista]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != normalize(nome_tabela):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
            ))
   
    if not erros_avaliacao:
        tipos_ev_raw = dados.get("tipo_envolvimento", [])
        tipos_ev_lista = []

        if isinstance(tipos_ev_raw, str):
            tipos_ev_lista = [normalize(tipos_ev_raw)]
        elif isinstance(tipos_ev_raw, list):
            for item in tipos_ev_raw:
                if isinstance(item, dict):
                    envolvimento = item.get("envolvimento", "")
                    tipos_ev_lista.append(normalize(envolvimento))
                elif isinstance(item, str):
                    tipos_ev_lista.append(normalize(item))

        if "fiel depositario" not in tipos_ev_lista:
            erros_avaliacao.append(tratar_mensagem_erro("Tipo de envolvimento 'fiel depositario' não encontrado."))  

    if not erros_avaliacao and isinstance(dados.get("tipo_situacao"), list):
        descricoes = [
            normalize(obj.get('dados', ''))
            for obj in dados['tipo_situacao']
        ]        

        if not any('apreendido por infracao penal' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Cadastro de objeto não possui o tipo 'Apreendido por infração penal'"
            ))

        if not any('deposito fiel' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Cadastro de objeto não possui o tipo 'Depósito fiel'"
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
        required_naturezas = [
            "sinistro de trânsito (com pessoa ferida ou morta)",
            "lesão corporal culposa em sinistro de trânsito",
            "posse ou porte de drogas para uso pessoal"
        ] 
        natureza_texto = dados.get("natureza", "")
        natureza_lista = [n.strip().lower() for n in natureza_texto.split(";") if n.strip()]        
        missing = [req for req in required_naturezas if req not in natureza_lista]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != normalize(nome_tabela):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
            ))

    if not erros_avaliacao:        
        relato_norm = normalize_str(dados.get("relato_policial", ""))
        relato_norm = " ".join(relato_norm.split())        
        frase_norm = normalize_str("comunica-se à autoridade judiciária competente")    
        if frase_norm not in relato_norm:
            erros_avaliacao.append(tratar_mensagem_erro(
                "Relato policial não contém o critério padrão de confecção por IA"
            ))  

    if not erros_avaliacao:           
        required_envolvidos = ["situação apreendida"] 
        drogas = dados.get("tipo_drogas", "").lower()
        missing = [req for req in required_envolvidos if req not in drogas]
        if missing:
            msg = f"Nenhum dos envolvidos possui o tipo de drogas solicitado: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))    
    
    if not erros_avaliacao:
        tipos_veiculos = ["apreendido por infracao penal", "deposito fiel"]
        tipo_ve_raw = dados.get("tipo_veiculos", "")
        if isinstance(tipo_ve_raw, list):
            tipo_ve_texto = "; ".join(str(item) for item in tipo_ve_raw).lower()
        else:
            tipo_ve_texto = str(tipo_ve_raw).lower()
        tipo_ve_lista = [normalize(item) for item in tipo_ve_texto.replace(',', ';').split(';') if item.strip()]
        missing = [req for req in tipos_veiculos if req not in tipo_ve_lista]
        if missing:
            msg = f"Veículos não possuem a condição de apreendido por infração penal e depósito fiel: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))   
   
    if not erros_avaliacao:
        tipos_ev_raw = dados.get("tipo_envolvimento", [])
        tipos_ev_lista = []

        if isinstance(tipos_ev_raw, str):
            tipos_ev_lista = [normalize(tipos_ev_raw)]
        elif isinstance(tipos_ev_raw, list):
            for item in tipos_ev_raw:
                if isinstance(item, dict):
                    envolvimento = item.get("envolvimento", "")
                    tipos_ev_lista.append(normalize(envolvimento))
                elif isinstance(item, str):
                    tipos_ev_lista.append(normalize(item))

        if "abordado" not in tipos_ev_lista:
            erros_avaliacao.append(tratar_mensagem_erro("Tipo de envolvimento 'abordado' não encontrado."))  
    
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

    
def corrigir_ppe(driver, tarefa, dados, erros_coleta):
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
        required_naturezas = ["dano", "posse ou porte de drogas para uso pessoal", "perturbação do trabalho ou sossego alheios", "porte ou posse de arma branca ou simulacro", "lesão corporal leve - dolosa"] 
        natureza_texto = dados.get("natureza", "")
        natureza_lista = [n.strip().lower() for n in natureza_texto.split(";") if n.strip()]        
        missing = [req for req in required_naturezas if req not in natureza_lista]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:        
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != normalize(nome_tabela):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
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
        required_envolvidos = ["situação apreendida"] 
        drogas = dados.get("tipo_drogas", "").lower()
        missing = [req for req in required_envolvidos if req not in drogas]
        if missing:
            msg = f"Nenhum dos envolvidos possui o tipo de drogas solicitado: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))     

    if not erros_avaliacao and isinstance(dados.get("tipo_situacao"), list):        
        descricoes = [normalize(obj['dados']) for obj in dados['tipo_situacao']]

        if not any('caixa' in desc and 'som' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Caixa de Som cadastrada"
            ))

        if not any(('mesa' in desc or 'controladora' in desc) and 'som' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Mesa controladora cadastrada"
            ))

        if not any('faca' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Faca cadastrada"
            ))

        if not any('portao' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Portão cadastrado"
            ))                
        
    if not erros_avaliacao and isinstance(dados.get("tipo_envolvimento"), list):
        tipo_env = dados.get("tipo_envolvimento", [])        

        if not tem_envolvimento_para_tipo(tipo_env, "paulo", "fiel depositario", "perturbacao do trabalho ou sossego alheios"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Paulo Confusão da Silva deveria estar com envolvimento 'Fiel depositário' para o tipo 'Perturbação do trabalho ou sossego alheios'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "paulo", "autor", "perturbacao do trabalho ou sossego alheios"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Paulo Confusão da Silva deveria estar com envolvimento 'Autor' para o tipo 'Perturbação do trabalho ou sossego alheios'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "paulo", "autor", "lesao corporal leve - dolosa"):           
            erros_avaliacao.append(tratar_mensagem_erro(
                "Paulo Confusão da Silva deveria estar com envolvimento 'Autor' para o tipo 'Lesão corporal leve - Dolosa'."
            ))
        if not tem_envolvimento(tipo_env, "paulo", "abordado"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Paulo Confusão da Silva deveria estar com envolvimento 'Abordado'."
            ))
        if not tem_envolvimento(tipo_env, "edilson", "abordado"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Edilson Faca na Cinta deveria estar com envolvimento 'Abordado'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "edilson", "autor", "porte ou posse de arma branca ou simulacro"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Edilson Faca na Cinta deveria estar com envolvimento 'Autor' para o tipo 'Porte ou posse de arma branca ou simulacro'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "edilson", "autor", "posse ou porte de drogas para uso pessoal"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Edilson Faca na Cinta deveria estar com envolvimento 'Autor' para o tipo 'Posse ou porte de drogas para uso pessoal'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "zeca", "abordado", "dano"):           
            erros_avaliacao.append(tratar_mensagem_erro(
                "Zeca Quebra Tudo deveria estar com envolvimento 'Abordado' para o tipo 'Dano'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "zeca", "autor", "dano"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Zeca Quebra Tudo deveria estar com envolvimento 'autor' para o tipo 'Dano'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "joaquim", "vitima", "lesao corporal leve - dolosa"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Joaquim Sossego de Almeida deveria estar com envolvimento 'Vítima' para o tipo 'Lesão corporal leve - Dolosa'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "idalina", "vitima", "dano"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Idalina Paz da Costa deveria estar com envolvimento 'Vítima' para o tipo 'Dano'."
            ))       

        
    if not erros_avaliacao:
        nota = 1
    
    return Resultado(
        atividade='PPE',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )

def corrigir_cfs25(driver, tarefa, dados, erros_coleta):
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
        required_naturezas = ["dano", "posse ou porte de drogas para uso pessoal", "perturbação do trabalho ou sossego alheios", "porte ou posse de arma branca ou simulacro", "lesão corporal leve - dolosa"] 
        natureza_texto = dados.get("natureza", "")
        natureza_lista = [n.strip().lower() for n in natureza_texto.split(";") if n.strip()]        
        missing = [req for req in required_naturezas if req not in natureza_lista]
        if missing:
            msg = f"Uma ou mais das naturezas obrigatórias não coletadas: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg))        
    
    if not erros_avaliacao:               
        comandante_extraido = dados.get("comandante_guarnicao", "")
        if normalize_str(comandante_extraido) != normalize(nome_tabela):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Comandante da guarnição não confere com o nome do aluno"
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
        required_envolvidos = ["situação apreendida"] 
        drogas = dados.get("tipo_drogas", "").lower()
        missing = [req for req in required_envolvidos if req not in drogas]
        if missing:
            msg = f"Nenhum dos envolvidos possui o tipo de drogas solicitado: {', '.join(missing)}"
            erros_avaliacao.append(tratar_mensagem_erro(msg)) 
                
    if not erros_avaliacao and isinstance(dados.get("tipo_situacao"), list):        
        descricoes = [normalize(obj['dados']) for obj in dados['tipo_situacao']]

        if not any('caixa' in desc and 'som' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Caixa de Som cadastrada"
            ))

        if not any(('mesa' in desc or 'controladora' in desc) and 'som' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Mesa controladora cadastrada"
            ))

        if not any('faca' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Faca cadastrada"
            ))

        if not any('portao' in desc for desc in descricoes):
            erros_avaliacao.append(tratar_mensagem_erro(
                "Ocorrência não possui Portão cadastrado"
            ))
        
    if not erros_avaliacao and isinstance(dados.get("tipo_envolvimento"), list):
        tipo_env = dados.get("tipo_envolvimento", [])        

        if not tem_envolvimento_para_tipo(tipo_env, "carlos", "fiel depositario", "perturbacao do trabalho ou sossego alheios"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Carlos da Bagunça Júnior deveria estar com envolvimento 'Fiel depositário' para o tipo 'Perturbação do trabalho ou sossego alheios'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "carlos", "autor", "perturbacao do trabalho ou sossego alheios"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Carlos da Bagunça Júnior deveria estar com envolvimento 'Autor' para o tipo 'Perturbação do trabalho ou sossego alheios'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "carlos", "autor", "lesao corporal leve - dolosa"):           
            erros_avaliacao.append(tratar_mensagem_erro(
                "Carlos da Bagunça Júnior deveria estar com envolvimento 'Autor' para o tipo 'Lesão corporal leve - Dolosa'."
            ))
        if not tem_envolvimento(tipo_env, "carlos", "abordado"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Carlos da Bagunça Júnior deveria estar com envolvimento 'Abordado'."
            ))
        if not tem_envolvimento(tipo_env, "elcio", "abordado"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Élcio da Navalha deveria estar com envolvimento 'Abordado'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "elcio", "autor", "porte ou posse de arma branca ou simulacro"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Élcio da Navalha deveria estar com envolvimento 'Autor' para o tipo 'Porte ou posse de arma branca ou simulacro'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "elcio", "autor", "posse ou porte de drogas para uso pessoal"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Élcio da Navalha deveria estar com envolvimento 'Autor' para o tipo 'Posse ou porte de drogas para uso pessoal'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "douglas", "abordado", "dano"):           
            erros_avaliacao.append(tratar_mensagem_erro(
                "Douglas Arremesso da Silva deveria estar com envolvimento 'Abordado' para o tipo 'Dano'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "douglas", "autor", "dano"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Douglas Arremesso da Silva deveria estar com envolvimento 'autor' para o tipo 'Dano'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "antonio", "vitima", "lesao corporal leve - dolosa"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Antônio Almeida do Sossego deveria estar com envolvimento 'Vítima' para o tipo 'Lesão corporal leve - Dolosa'."
            ))
        if not tem_envolvimento_para_tipo(tipo_env, "margarida", "vitima", "dano"):            
            erros_avaliacao.append(tratar_mensagem_erro(
                "Margarida da Paz deveria estar com envolvimento 'Vítima' para o tipo 'Dano'."
            ))       

        
    if not erros_avaliacao:
        nota = 1
    
    return Resultado(
        atividade='CFS25',
        protocolo=protocolo,
        re=re_valor,
        nome=nome_tabela,
        pelotao=tarefa.pelotao,
        dados={k: str(v) for k, v in dados.items()},
        nota=nota,
        erros_coleta=erros_coleta,
        erros_avaliacao=erros_avaliacao
    )