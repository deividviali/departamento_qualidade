import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.helpers import normalize_space, tratar_mensagem_erro, fechar_popup

def tratar_mensagem_erro(mensagem):
    return mensagem.split(":")[0] if ":" in mensagem else mensagem

def interagir_com_iframe(navegador, iframe_index, xpath, valor):
    try:
        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
        navegador.switch_to.frame(iframes[iframe_index])
        elem = WebDriverWait(navegador, 15).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        elem.clear()
        elem.send_keys(valor)
        return True
    except Exception as e:
        erro_msg = tratar_mensagem_erro(f"Erro ao interagir com o elemento: {e}")
        print(erro_msg)
        navegador.save_screenshot("erro_interacao_iframe.png")
        return False
    finally:
        navegador.switch_to.default_content()

def interagir_com_iframe_botao(navegador, iframe_index, xpath_elemento):
    try:
        iframes = navegador.find_elements(By.TAG_NAME, "iframe")
        navegador.switch_to.frame(iframes[iframe_index])
        elemento = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_elemento))
        )
        elemento.click()
    except Exception as e:
        erro_msg = tratar_mensagem_erro(f"Erro ao interagir com o botão: {e}")
        print(erro_msg)
        navegador.save_screenshot("erro_interacao_botao.png")
    finally:
        navegador.switch_to.default_content()

def fechar_popup(driver):   
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ui-dialog-titlebar-close"))
        )
        close_button.click()
        time.sleep(1)
    except Exception as e:
        print(tratar_mensagem_erro(f"Erro ao fechar popup: {e}"))

def extrair_campos(driver, xpaths_campos, erros_coleta):
    dados = {}
    for campo, xpath in xpaths_campos.items():
        try:
            elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
            dados[campo] = normalize_space(elem.text)
        except Exception as e:
            msg = f"Erro extraindo {campo}: {e}"
            erros_coleta.append(tratar_mensagem_erro(msg))
            dados[campo] = ""
    return dados

# def extrair_envolvidos_e_tipos(driver, erros_coleta):      
#     envolvidos = []
#     tipos_envolvimento = []
#     WebDriverWait(driver, 30).until(
#         EC.presence_of_all_elements_located((By.XPATH, "//a[@id='dialogDetalhesEnvolvido']"))
#     )
#     anchors = driver.find_elements(By.XPATH, "//a[@id='dialogDetalhesEnvolvido']")
#     for index, anchor in enumerate(anchors, start=1):        
#         try:
#             linha = anchor.find_element(By.XPATH, "./ancestor::tr")
#             texto = linha.find_element(By.XPATH, "./td[2]").text.strip()
#             if texto:
#                 envolvidos.append(texto)
#         except Exception as e:
#             erros_coleta.append(tratar_mensagem_erro(f"Erro extraindo envolvido na linha {index}: {e}"))
#         try:
#             anchor.click()
#             iframe = WebDriverWait(driver, 40).until(
#                 EC.frame_to_be_available_and_switch_to_it(
#                     (By.XPATH, "//iframe[contains(@src, '/sade/sade/public/pessoas/view/')]")
#                 )
#             )
#             time.sleep(4)
#             linhas = WebDriverWait(driver, 15).until(
#                 EC.presence_of_all_elements_located((By.XPATH, "//table[@id='gridListEnvolvimento']/tbody/tr"))
#             )

#             for index, linha in enumerate(linhas, start=1):
#                 try:
#                     colunas = linha.find_elements(By.TAG_NAME, "td")

#                     if len(colunas) >= 2:
#                         envolvimento = normalize_space(colunas[0].text)
#                         tipo_raw = colunas[1].get_attribute("innerText")  # captura texto visível (mesmo com img)
#                         tipo_atendimento = normalize_space(tipo_raw)

#                         tipos_envolvimento.append({
#                             "texto": envolvimento,
#                             "tipos": tipo_atendimento
#                         })
#                     else:
#                         erros_coleta.append(tratar_mensagem_erro(
#                             f"Linha {index} da tabela de envolvimento não possui ao menos 2 colunas"
#                         ))
#                 except Exception as e:
#                     erros_coleta.append(tratar_mensagem_erro(
#                         f"Erro ao processar linha {index} da tabela de envolvimento: {e}"
#                     ))

#         except Exception as e:
#             if index == 1:
#                 msg = f"Erro ao coletar o tipo de envolvimento do primeiro registro (linha {index}): {e}"
#                 print(tratar_mensagem_erro(msg))
#                 erros_coleta.append(tratar_mensagem_erro(msg))
#             tipos_envolvimento.append({"texto": texto, "tipos": ""})
#         finally:
#             driver.switch_to.default_content()
#             fechar_popup(driver)
#     return envolvidos, tipos_envolvimento


def extrair_envolvidos_e_tipos(driver, erros_coleta):      
    envolvidos = []
    tipos_envolvimento = []

    WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[@id='dialogDetalhesEnvolvido']"))
    )
    anchors = driver.find_elements(By.XPATH, "//a[@id='dialogDetalhesEnvolvido']")

    for index, anchor in enumerate(anchors, start=1):        
        nome_envolvido = ""
        try:
            linha = anchor.find_element(By.XPATH, "./ancestor::tr")
            nome_envolvido = linha.find_element(By.XPATH, "./td[2]").text.strip()
            if nome_envolvido:
                envolvidos.append(nome_envolvido)
        except Exception as e:
            erros_coleta.append(tratar_mensagem_erro(f"Erro extraindo envolvido na linha {index}: {e}"))
            nome_envolvido = f"Indefinido_{index}"

        try:
            anchor.click()
            iframe = WebDriverWait(driver, 40).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[contains(@src, '/sade/sade/public/pessoas/view/')]")
                )
            )
            time.sleep(4)
            linhas = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//table[@id='gridListEnvolvimento']/tbody/tr"))
            )

            for i, linha in enumerate(linhas, start=1):
                try:
                    colunas = linha.find_elements(By.TAG_NAME, "td")

                    if len(colunas) >= 2:
                        envolvimento = normalize_space(colunas[0].text)
                        tipo_raw = colunas[1].get_attribute("innerText")  # texto visível mesmo com imagens
                        tipo_atendimento = normalize_space(tipo_raw)

                        tipos_envolvimento.append({
                            "nome": nome_envolvido,
                            "envolvimento": envolvimento,
                            "tipos": tipo_atendimento
                        })
                    else:
                        erros_coleta.append(tratar_mensagem_erro(
                            f"Linha {i} da tabela de envolvimento não possui ao menos 2 colunas"
                        ))
                except Exception as e:
                    erros_coleta.append(tratar_mensagem_erro(
                        f"Erro ao processar linha {i} da tabela de envolvimento: {e}"
                    ))
        except Exception as e:
            if index == 1:
                msg = f"Erro ao abrir popup do tipo de envolvimento (linha {index}): {e}"
                print(tratar_mensagem_erro(msg))
                erros_coleta.append(tratar_mensagem_erro(msg))
            tipos_envolvimento.append({
                "nome": nome_envolvido,
                "envolvimento": "",
                "tipos": ""
            })
        finally:
            driver.switch_to.default_content()
            fechar_popup(driver)

    return envolvidos, tipos_envolvimento


def extrair_veiculos_e_detalhes(driver, erros_coleta):
    veiculos = []
    tipos_veiculos = []
    try:
        print("🔍 Iniciando extração de veículos...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[contains(@class,'table-striped') and contains(@class,'table-bordered')]"))
        )
        tables = driver.find_elements(By.XPATH, "//table[contains(@class,'table-striped') and contains(@class,'table-bordered')]")
        for tbl in tables:
            headers = tbl.find_elements(By.XPATH, ".//thead/tr/th")
            idx_placa = next((i+1 for i, th in enumerate(headers) if "placa" in th.text.lower()), None)
            if not idx_placa:
                continue
            linhas = tbl.find_elements(By.XPATH, ".//tbody/tr")
            for index, linha in enumerate(linhas, start=1):
                try:
                    print(f"\n🔎 Processando linha {index}...")
                    placa_veiculo = linha.find_element(By.XPATH, f"./td[{idx_placa}]").text.strip()
                    veiculos.append(placa_veiculo)
                    anchor = linha.find_element(By.XPATH, ".//a[contains(@class, 'dialogDetalhes')]")                    
                    anchor.click()
                    WebDriverWait(driver, 40).until(
                        EC.frame_to_be_available_and_switch_to_it(
                            (By.XPATH, "//iframe[contains(@src, '/sade/sade/public/veiculos/view/')]")
                        )
                    )
                    time.sleep(2)
                    elementos = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//body/div/div[1]/div[5]"))
                    )
                    tipos = [normalize_space(elem.text) for elem in elementos if elem.text.strip()]
                    tipos_veiculos.append("; ".join(tipos) if tipos else "")
                except Exception as e:
                    msg = f"❌ Erro ao extrair detalhes do veículo na linha {index}: {e}"
                    print(tratar_mensagem_erro(msg))
                    erros_coleta.append(tratar_mensagem_erro(msg))
                    veiculos.append("")
                    tipos_veiculos.append("")
                finally:
                    driver.switch_to.default_content()
                    fechar_popup(driver)
    except Exception as e:
        msg = f"❌ Erro geral ao extrair veículos: {e}"
        print(tratar_mensagem_erro(msg))
        erros_coleta.append(tratar_mensagem_erro(msg))
    return "; ".join(veiculos), tipos_veiculos

def extrair_armas_e_detalhes(driver, erros_coleta):
    armas = []
    tipos_armas = []
    try:
        print("🔍 Iniciando extração de armas...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[contains(@class,'table-striped') and contains(@class,'table-bordered')]"))
        )
        tables = driver.find_elements(By.XPATH, "//table[contains(@class,'table-striped') and contains(@class,'table-bordered')]")
        for tbl in tables:
            headers = tbl.find_elements(By.XPATH, ".//thead/tr/th")
            idx_calibre = next((i+1 for i, th in enumerate(headers) if "calibre" in th.text.lower()), None)
            if not idx_calibre:
                continue
            linhas = tbl.find_elements(By.XPATH, ".//tbody/tr")
            for index, linha in enumerate(linhas, start=1):
                try:                    
                    info_arma = linha.find_element(By.XPATH, f"./td[{idx_calibre}]").text.strip()
                    armas.append(info_arma)
                    anchor = linha.find_element(By.XPATH, ".//a[contains(@class, 'dialogDetalhes')]")                   
                    anchor.click()
                    WebDriverWait(driver, 40).until(
                        EC.frame_to_be_available_and_switch_to_it(
                            (By.XPATH, "//iframe[contains(@src, '/sade/sade/public/armas/view/')]")
                        )
                    )
                    time.sleep(2)
                    elementos = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//body/div/div"))
                    )
                    tipos = [normalize_space(elem.text) for elem in elementos if elem.text.strip()]
                    tipos_armas.append("; ".join(tipos) if tipos else "")
                except Exception as e:
                    msg = f"❌ Erro ao extrair detalhes da arma na linha {index}: {e}"
                    print(tratar_mensagem_erro(msg))
                    erros_coleta.append(tratar_mensagem_erro(msg))
                    armas.append("")
                    tipos_armas.append("")
                finally:
                    driver.switch_to.default_content()
                    fechar_popup(driver)
    except Exception as e:
        msg = f"❌ Erro geral ao extrair arma: {e}"
        print(tratar_mensagem_erro(msg))
        erros_coleta.append(tratar_mensagem_erro(msg))
    return "; ".join(armas), tipos_armas

def extrair_drogas_e_detalhes(driver, erros_coleta):
    drogas = []
    tipos_drogas = []
    try:        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Drogas')]"))
        )
        tabelas_drogas = driver.find_elements(
            By.XPATH,
            "//label[contains(text(), 'Drogas')]/following::table[contains(@class, 'table-striped') and contains(@class, 'table-bordered')]"
        )
        if not tabelas_drogas:            
            return "; ".join(drogas), tipos_drogas
        tbl = tabelas_drogas[0]
        ths = tbl.find_elements(By.XPATH, ".//thead/tr/th")
        idx_tipo = None
        idx_detalhes = None
        for i, th in enumerate(ths, start=1):
            cabecalho = th.text.strip().lower()
            if "tipo" in cabecalho:
                idx_tipo = i
            elif "detalhes" in cabecalho:
                idx_detalhes = i
        if not idx_tipo or not idx_detalhes:           
            return "; ".join(drogas), tipos_drogas
        linhas = tbl.find_elements(By.XPATH, ".//tbody/tr")
        for row_index, linha in enumerate(linhas, start=1):
            try:
                tipo_text = linha.find_element(By.XPATH, f"./td[{idx_tipo}]").text.strip()
                drogas.append(tipo_text)
                anchor = linha.find_element(By.XPATH, f"./td[{idx_detalhes}]//a")                
                anchor.click()
                WebDriverWait(driver, 40).until(
                    EC.frame_to_be_available_and_switch_to_it(
                        (By.XPATH, "//iframe[contains(@src, '/sade/sade/public/drogas/view/')]")
                    )
                )
                time.sleep(2)
                elementos = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//body/div/div"))
                )
                tipos = [normalize_space(elem.text) for elem in elementos if elem.text.strip()]
                tipos_drogas.append("; ".join(tipos) if tipos else "")
            except Exception as e:
                msg = f"❌ Erro ao extrair detalhes da droga na linha {row_index}: {e}"
                print(tratar_mensagem_erro(msg))
                erros_coleta.append(tratar_mensagem_erro(msg))
                drogas.append("")
                tipos_drogas.append("")
            finally:
                driver.switch_to.default_content()
                fechar_popup(driver)
    except Exception as e:
        msg = f"❌ Erro geral ao extrair drogas: {e}"
        print(tratar_mensagem_erro(msg))
        erros_coleta.append(tratar_mensagem_erro(msg))
    return "; ".join(drogas), tipos_drogas


def extrair_tipo_situacao(driver, erros_coleta):      
    objetos = []
    tipo_situacao = []

    WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'dialogDetalhesObjetoDiverso') and contains(@class, 'dialogDetalhes')]"))
    )
    anchors = driver.find_elements(By.XPATH, "//a[contains(@class, 'dialogDetalhesObjetoDiverso') and contains(@class, 'dialogDetalhes')]")

    for index, anchor in enumerate(anchors, start=1):
        try:
            linha = anchor.find_element(By.XPATH, "./ancestor::tr")
            texto_objeto = linha.find_element(By.XPATH, "./td[1]").text.strip()
            objetos.append(texto_objeto)
        except Exception as e:
            objetos.append("")
            erros_coleta.append(tratar_mensagem_erro(f"Erro extraindo objeto na linha {index}: {e}"))

        try:
            anchor.click()

            iframe = WebDriverWait(driver, 40).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[contains(@src, '/sade/sade/public/objetos/view/')]")
                )
            )
            time.sleep(2)

            elementos = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div/div[2]"))
            )           

            dados = [normalize_space(elem.text) for elem in elementos if elem.text.strip()]
            dados_str = "; ".join(dados)

            tipo_situacao.append({
                "objeto": texto_objeto,
                "dados": dados_str
            })


        except Exception as e:
            msg = f"Erro ao coletar tipo de situação na linha {index}: {e}"
            print(tratar_mensagem_erro(msg))
            erros_coleta.append(tratar_mensagem_erro(msg))
            tipo_situacao.append("")
        finally:
            driver.switch_to.default_content()
            fechar_popup(driver)

    return objetos, tipo_situacao

def extrair_naturezas(driver) -> str:
    resultados = []
    tables = driver.find_elements(By.XPATH, "//table[contains(@class,'table-striped') and contains(@class,'table-bordered')]")
    for tbl in tables:
        headers = tbl.find_elements(By.XPATH, ".//thead/tr/th")
        idx = next((i+1 for i, th in enumerate(headers) if th.text.strip().lower() == "natureza"), None)
        if not idx:
            continue
        cells = tbl.find_elements(By.XPATH, f".//tbody/tr/td[{idx}]")
        for cell in cells:
            txt = normalize_space(cell.text)
            if txt:
                resultados.append(txt)
    if not resultados:
        raise ValueError("Nenhuma tabela com cabeçalho 'Natureza' encontrada.")
    return "; ".join(resultados)

def extrair_comandante(driver) -> str:
    resultados = []
    tables = driver.find_elements(By.XPATH, "//table[contains(@class,'table-striped') and contains(@class,'table-bordered')]")
    for tbl in tables:
        headers = tbl.find_elements(By.XPATH, ".//thead/tr/th")
        idx = next((i+1 for i, th in enumerate(headers) if th.text.strip().lower() == "comandante"), None)
        if not idx:
            continue
        cells = tbl.find_elements(By.XPATH, f".//tbody/tr/td[{idx}]")
        for cell in cells:
            txt = normalize_space(cell.text)
            if txt:
                resultados.append(txt)
    if not resultados:
        raise ValueError("Nenhuma tabela com cabeçalho 'comandante' encontrada.")
    return "; ".join(resultados)

def coletar_a(driver, protocolo, erros_coleta):    
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Consultas"))
        ).click()
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Ocorrências"))
        ).click()
        time.sleep(10)
        campo_prot = "/html/body/form/div[1]/div/div[2]/div[1]/div[3]/div[2]/div[1]/div/input"
        if not interagir_com_iframe(driver, 0, campo_prot, protocolo):
            erros_coleta.append("Protocolo não encontrado no iframe de busca")
            return {}
        interagir_com_iframe_botao(driver, 0, "/html/body/form/div[2]/div/button[1]")
        time.sleep(1)
        interagir_com_iframe_botao(driver, 0, "/html/body/div[5]/div[2]/div[3]/button")
        time.sleep(2)

        # Abre detalhes do protocolo
        try:
            interagir_com_iframe_botao(driver, 0, "//table/tbody/tr/td[10]/a[1]")
        except:
            interagir_com_iframe_botao(driver, 0, "//table/tbody/tr[1]/td[10]/a[1]")
        time.sleep(1)
        original = driver.current_window_handle
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(1)
       
        xpaths = {
            "nome_geracao": "/html/body/div[9]/div[2]",
            "info_protocolo": "/html/body/div[1]/label",
            "codigo_fechamento": "/html/body/div[24]/div[2]",
            "origem_abertura_oc": "/html/body/div[15]/div[2]",
            "data_oc": "/html/body/div[1]/label",
            "relato_policial": "/html/body/div[26]/div[2]",
            "complemento_oc": "/html/body/div[11]/table/tbody/tr/td"

        }
        dados = extrair_campos(driver, xpaths, erros_coleta)   

        try:
            dados["natureza"] = extrair_naturezas(driver)
        except Exception as e:
            erros_coleta.append(tratar_mensagem_erro(f"Erro extraindo Natureza: {e}"))
            dados["natureza"] = ""   

        try:
            dados["comandante_guarnicao"] = extrair_comandante(driver)
        except Exception as e:
            erros_coleta.append(tratar_mensagem_erro(str(e)))
            dados["comandante_guarnicao"] = ""                   
        if dados["comandante_guarnicao"]:
            lista_comandantes = [cmd.strip() for cmd in dados["comandante_guarnicao"].split(";") if cmd.strip()]
            lista_comandantes_unicas = list(dict.fromkeys(lista_comandantes))
            dados["comandante_guarnicao"] = "; ".join(lista_comandantes_unicas)

        try:            
            veiculos_str, tipo_veiculos = extrair_veiculos_e_detalhes(driver, erros_coleta)            
            dados["veiculos"] = veiculos_str
            dados["tipo_veiculos"] = "; ".join(tipo_veiculos)
        except Exception as e:
            msg = f"Erro ao extrair veículos: {e}"
            print(tratar_mensagem_erro(msg))
            erros_coleta.append(tratar_mensagem_erro(msg))
            dados["veiculos"] = ""
            dados["tipo_veiculos"] = ""
            
        try:            
            armas_str, tipo_armas = extrair_armas_e_detalhes(driver, erros_coleta)            
            dados["armas"] = armas_str
            dados["tipo_armas"] = "; ".join(tipo_armas)
        except Exception as e:
            msg = f"Erro ao extrair Armas: {e}"
            print(tratar_mensagem_erro(msg))
            erros_coleta.append(tratar_mensagem_erro(msg))
            dados["armas"] = ""
            dados["tipo_armas"] = ""
            
        try:            
            drogas_str, tipo_drogas = extrair_drogas_e_detalhes(driver, erros_coleta)
            dados["drogas"] = drogas_str
            dados["tipo_drogas"] = "; ".join(tipo_drogas)
        except Exception as e:
            msg = f"Erro ao extrair Drogas: {e}"
            print(tratar_mensagem_erro(msg))
            erros_coleta.append(tratar_mensagem_erro(msg))
            dados["drogas"] = ""
            dados["tipo_drogas"] = ""

        try:
            env_str, env_tipos = extrair_envolvidos_e_tipos(driver, erros_coleta)
            dados["envolvido"] = env_str
            dados["tipo_envolvimento"] = env_tipos
        except Exception as e:
            erros_coleta.append(tratar_mensagem_erro(str(e)))
            dados["envolvido"] = dados["tipo_envolvimento"] = ""

        if "nome_geracao" in dados:
                    nome_geracao = dados["nome_geracao"]
                    nome_match = re.search(r"^(.*?)\s*\[", nome_geracao)
                    if nome_match:
                        dados["nome_geracao"] = nome_match.group(1).strip()
        if "protocolo" in dados:
            info_protocolo = dados["protocolo"].replace("Ocorrência Protocolo:", "").strip()
            prot_match = re.search(r"^(.*?)\s*\[", info_protocolo)
            if prot_match:
                dados["protocolo"] = prot_match.group(1).strip()

        try:
            objetos_str, tipo_situacao = extrair_tipo_situacao(driver, erros_coleta)
            dados["objetos"] = objetos_str
            dados["tipo_situacao"] = tipo_situacao            
        except Exception as e:
            msg = f"Erro ao extrair objetos: {e}"
            print(tratar_mensagem_erro(msg))
            erros_coleta.append(tratar_mensagem_erro(msg))
            dados["objetos"] = ""
            dados["tipo_situacao"] = ""       
        
        driver.close()
        driver.switch_to.window(original)
        return dados
    

def coletar_b(driver, protocolo, erros_coleta):
    return coletar_a(driver, protocolo, erros_coleta)

def coletar_c(driver, protocolo, erros_coleta):
    return coletar_a(driver, protocolo, erros_coleta)

def coletar_d(driver, protocolo, erros_coleta):
    return coletar_a(driver, protocolo, erros_coleta)

def coletar_e(driver, protocolo, erros_coleta):
    return coletar_a(driver, protocolo, erros_coleta)

def coletar_f(driver, protocolo, erros_coleta):
    return coletar_a(driver, protocolo, erros_coleta)

def coletar_ppe(driver, protocolo, erros_coleta):
    return coletar_a(driver, protocolo, erros_coleta)
    

