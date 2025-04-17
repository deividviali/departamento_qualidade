import re


def tratar_mensagem_erro(mensagem: str) -> str:
    return mensagem.split(':')[0] if ':' in mensagem else mensagem


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def fechar_popup(driver) -> None:
    try:
        btn = driver.find_element_by_css_selector("button.ui-dialog-titlebar-close")
        btn.click()
    except:
        pass