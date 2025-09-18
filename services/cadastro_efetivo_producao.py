# services/cadastro_efetivo_producao.py

import time
from sqlalchemy import text
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# Função para interagir com campos dentro de iframes
def interagir_com_iframe(driver, iframe_index, xpath, valor):
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if not iframes or iframe_index >= len(iframes):
        print(f"[ERRO] Nenhum iframe encontrado no índice {iframe_index}")
        return False

    driver.switch_to.frame(iframes[iframe_index])
    try:
        elem = driver.find_element(By.XPATH, xpath)
        elem.clear()
        elem.send_keys(str(valor))
    except Exception as e:
        print(f"Erro ao interagir com elemento: {e}")
    finally:
        driver.switch_to.default_content()

def interagir_com_iframe_botao(driver, iframe_index, xpath_elemento):
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        driver.switch_to.frame(iframes[iframe_index])
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath_elemento))
        )
        driver.find_element(By.XPATH, xpath_elemento).click()
    except Exception as e:
        print(f"Erro ao interagir com o botão: {e}")
    finally:
        driver.switch_to.default_content()

def interagir_com_iframe_select_option(driver, iframe_index, xpath_option):
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframes[iframe_index])
    try:
        option_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_option))
        )
        option_element.click()
    except Exception as e:
        print(f"Erro ao interagir com o elemento de seleção: {e}")
    finally:
        driver.switch_to.default_content()


def buscar_unidade_siseg(engine, unidade_nome: str):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT unidade_siseg
            FROM unidades
            WHERE nomenclatura_unidade LIKE :nome
            LIMIT 1
        """), {"nome": f"%{unidade_nome}%"}).fetchone()
    return result.unidade_siseg if result else None


def buscar_referencia_unidade_db(engine, unidade_nome: str):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, nomenclatura_unidade
            FROM unidades
            WHERE nomenclatura_unidade LIKE :nomenclatura_unidade
            LIMIT 1
        """), {"nomenclatura_unidade": f"%{unidade_nome}%"}).mappings().fetchone()
    return result if result else None


def atualizar_efetivo(engine_main, status_msgs: list, matriculas: list, driver):
    with engine_main.connect() as conn:
        militares = conn.execute(text("""
            SELECT matricula, graduacao, nome_militar, nome_guerra, telefone, unidade_nome
            FROM dados_importados_militar
            WHERE tipo = 'efetivo' AND matricula IN :matriculas
        """), {"matriculas": tuple(matriculas)}).fetchall()

    status_msgs.append(f"🔎 {len(militares)} militares encontrados para atualização.")   
    
        

    for militar in militares:
        try:
            status_msgs.append(f"➡️ Processando matrícula {militar.matricula}...")

            referencia_unidade = buscar_referencia_unidade_db(engine_main, militar.unidade_nome)
            if not referencia_unidade:
                msg = f"❌ Unidade não encontrada: {militar.unidade_nome}"
                status_msgs.append(msg)                
                continue            

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Cadastros"))).click()
            time.sleep(4)

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Efetivo"))).click()
            time.sleep(4)

            # Pesquisar pela matrícula
            interagir_com_iframe(driver, 0, "//input[@id='MATRICULA']", str(militar.matricula))
            time.sleep(1)

            # Pesquisar
            interagir_com_iframe_botao(driver, 0, "//input[@id='pesquisar']")
            time.sleep(3)

            #Verifica iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"[DEBUG] Total de iframes na página: {len(iframes)}")
            for i, f in enumerate(iframes):
                print(f" - iframe {i}: {f.get_attribute('id')} {f.get_attribute('name')}")

            #acessa iframe
            driver.switch_to.frame("iframeContainer")
            try:
                # Tenta achar link "Editar" (se existir dentro da tabela)
                botoes_editar = driver.find_elements(By.XPATH, "//img[@title='Editar' or @alt='Editar']")
                if botoes_editar:
                    botoes_editar[0].click()
                    status_msgs.append(f"✏️ Editando efetivo {militar.matricula}")
                else:
                    # Se não tem Editar, clica no link "Novo"
                    botao_novo = driver.find_elements(By.ID, "btnNovo")
                    if botao_novo:
                        botao_novo[0].click()
                        status_msgs.append(f"➕ Criando novo efetivo {militar.matricula}")
                    else:
                        status_msgs.append("❌ Nenhum botão Editar ou Novo encontrado")
            finally:
                driver.switch_to.default_content()                

            #insere a Matricula
            interagir_com_iframe(driver, 0, "//input[@id='MATRICULA']", str(militar.matricula))
            time.sleep(1)
            
            #insere o nome completo
            interagir_com_iframe(driver, 0, "//input[@id='NOME']", str(militar.nome_militar)) 
            time.sleep(1)

            #insere o nome de guerra
            interagir_com_iframe(driver, 0, "//input[@id='NOME_DE_GUERRA']", str(militar.nome_guerra)) 
            time.sleep(1)

            #Insere Matricula
            matricula_invertida = ''.join(reversed(str(militar.matricula)))
            
            interagir_com_iframe(driver, 0, "//input[@id='SENHA']", str(matricula_invertida)) 
            time.sleep(1)

            interagir_com_iframe(driver, 0, "//input[@id='CONFIRMAR_SENHA']", str(matricula_invertida)) 
            time.sleep(1)

            #insere o telefone
            interagir_com_iframe(driver, 0, "//input[@id='TELEFONE']", str(militar.telefone)) 
            time.sleep(1)

            #insere o Posto/Graduação
            interagir_com_iframe(driver, 0, "//input[@id='POSTO_GRADUACAO']", str(militar.graduacao)) 
            time.sleep(1)            
            
            # Busca o código correto no banco
            unidade_siseg = buscar_unidade_siseg(engine_main, militar.unidade_nome)
            if not unidade_siseg:
                status_msgs.append(f"❌ Unidade não encontrada para {militar.unidade_nome}")
            else:
                status_msgs.append(f"🔗 Unidade mapeada: {militar.unidade_nome} → {unidade_siseg}")
                driver.switch_to.frame("iframeContainer")
                try:
                    ##SELECIONA AGENCIA                    
                    select_element = Select(driver.find_element(By.ID, "CRYPT_ID_AGENCIA"))
                    select_element.select_by_visible_text("PM")
                    time.sleep(4)


                    #SELECIONA UNIDADE
                    select_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "CRYPT_ID_UNIDADE"))  # ajuste o ID real do <select>
                    )
                    Select(select_element).select_by_visible_text(unidade_siseg)
                    status_msgs.append(f"✅ Unidade {unidade_siseg} selecionada no SISEG")
                    time.sleep(1)

                except Exception as e:
                    status_msgs.append(f"❌ Falha ao selecionar unidade {unidade_siseg}: {e}")
                finally:
                    driver.switch_to.default_content()              

        
            # Salvar alterações
            interagir_com_iframe_botao(driver, 0, "//input[@id='salvar']")
            time.sleep(2)
            interagir_com_iframe_botao(driver, 0, "//input[@id='popup_ok']") 

            with engine_main.begin() as conn:
                conn.execute(text("""
                    INSERT INTO cadastro_siseg
                        (tipo, matricula, nome_militar, status, data_cadastro)
                    VALUES
                        (:tipo, :matricula, :nome_militar, :status, NOW())
                """), {
                    "tipo": "atualizacao" if botoes_editar else "inclusao",
                    "matricula": militar.matricula,
                    "nome_militar": militar.nome_militar,
                    "status": "Processado"                              
                })


            msg = f"Efetivo atualizado - Matrícula {militar.matricula}"           
            status_msgs.append(f"✅ {msg}")

            
        except Exception as e:
            conn.execute(text("""
                INSERT INTO cadastro_siseg
                    (tipo, matricula, nome_militar, status, data_cadastro)
                VALUES
                    (:tipo, :matricula, :nome_militar, :status, NOW())
            """), {
                "tipo": "falha de sistema",
                "matricula": militar.matricula,
                "nome_militar": militar.nome_militar,                
                "status": "Não processado"
            })
            msg = f"❌ Falha ao processar {militar.matricula}: {str(e)}"
            status_msgs.append(msg)
            

    driver.quit()
    status_msgs.append("🏁 Atualização concluída.")
    return status_msgs






#debuga iframe
# inputs = driver.find_elements(By.TAG_NAME, "input")
# for i, inp in enumerate(inputs):
#     print(f"[DEBUG] INPUT {i}: id={inp.get_attribute('id')} name={inp.get_attribute('name')} title={inp.get_attribute('title')} value={inp.get_attribute('value')} type={inp.get_attribute('type')}")

# # Lista links
# links = driver.find_elements(By.TAG_NAME, "a")
# for i, a in enumerate(links):
#     print(f"[DEBUG] LINK {i}: text={a.text} title={a.get_attribute('title')} href={a.get_attribute('href')}")





























