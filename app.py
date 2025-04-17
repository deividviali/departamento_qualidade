from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file
from services.login_service import iniciar_navegador, efetuar_login
from services.orquestracao_service import orquestrar_tarefas
from utils.db import get_student, save_result, init_db
from models.tarefa import Tarefa
import sqlite3
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from config.settings import DB_PATH_TEMPLATE
from flask import Response, stream_with_context, render_template
import json


app = Flask(__name__)
app.secret_key = 'troque_para_uma_chave_secreta_segura'

ATIVIDADES_OPCOES = {
    '1': ('A', 'Atividade 1'),
    '2': ('B', 'Atividade 2'),
    '3': ('C', 'Atividade 3'),
}

@app.before_request
def setup_db():
    for tipo, _ in ATIVIDADES_OPCOES.values():
        init_db(tipo)

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        re_val = request.form.get('re', '').strip()
        student = get_student('A', re_val)
        if student:
            session['re'] = re_val
            session['nome'], session['pelotao'] = student
            return redirect(url_for('analyze'))
        else:
            flash('RE não encontrado.', 'error')
    return render_template('login.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if 're' not in session:
        return redirect(url_for('login'))

    # Quando for GET, só renderiza a página de seleção:
    if request.method == 'GET':
        return render_template('analyze.html',
                               options=ATIVIDADES_OPCOES,
                               re=session.get('re'))

    # === A partir daqui é POST ===
    # 1) Validações iniciais
    re_val = request.form.get('re', session['re']).strip()
    protocolo = request.form.get('protocolo', '').strip()
    if not protocolo:
        flash('Protocolo é obrigatório.', 'error')
        return render_template('analyze.html',
                               options=ATIVIDADES_OPCOES,
                               re=session['re'])

    # 2) AQUI definimos 'escolhas'
    escolhas = request.form.getlist('atividades')
    if not escolhas:
        flash('Selecione ao menos uma atividade.', 'error')
        return render_template('analyze.html',
                               options=ATIVIDADES_OPCOES,
                               re=session['re'])

    # 3) Traduzimos para os tipos reais (A, B, C…)
    tipos = [ATIVIDADES_OPCOES[ch][0] for ch in escolhas if ch in ATIVIDADES_OPCOES]

    # 4) Executa Selenium / orquestração
    driver = iniciar_navegador(headless=False)
    efetuar_login(driver)
    tarefa = Tarefa(
        protocolo=protocolo,
        re=session['re'],
        nome=session['nome'],
        pelotao=session['pelotao'],
        atividades=tipos
    )

    resultados = orquestrar_tarefas(driver, tarefa)
    for tipo, resultado in zip(tipos, resultados):
        save_result(tipo, resultado)
    driver.quit()

    # 5) Renderiza o resultado final
    return render_template('result.html', resultados=resultados)


from io import BytesIO
import pandas as pd

# Ajuste na view /report:
@app.route('/report')
def report():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']
    conn = sqlite3.connect(DB_PATH_TEMPLATE.format(atividade='A'))
    df = pd.read_sql_query(
        "SELECT protocolo, erros_avaliacao, nota, '' AS atividade FROM results WHERE re = ?",
        conn, params=(re_val,)
    )
    conn.close()
    # Preenche status e define atividade (ex: 'A'; se dinâmico, use coluna real)
    df['status'] = df['nota'].map({1:'certo', 0:'errado'})
    df['atividade'] = 'A'
    data = df[['atividade','protocolo','status','erros_avaliacao']] \
             .to_dict(orient='records')
    return render_template('report.html', data=data, re=re_val)


@app.route('/download_excel')
def download_excel():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']
    conn = sqlite3.connect(DB_PATH_TEMPLATE.format(atividade='A'))
    df = pd.read_sql_query(
        "SELECT protocolo, nota, erros_avaliacao FROM results WHERE re = ?", 
        conn, params=(re_val,)
    )
    conn.close()
    df['status'] = df['nota'].map({1: 'certo', 0: 'errado'})
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        download_name=f"relatorio_{re_val}.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    

@app.route('/download_pdf')
def download_pdf():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']
    conn = sqlite3.connect(DB_PATH_TEMPLATE.format(atividade='A'))
    df = pd.read_sql_query(
        "SELECT protocolo, nota, erros_avaliacao FROM results WHERE re = ?", 
        conn, params=(re_val,)
    )
    conn.close()
    df['status'] = df['nota'].map({1: 'certo', 0: 'errado'})

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    data = [list(df.columns)] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f"relatorio_{re_val}.pdf",
        as_attachment=True,
        mimetype='application/pdf'
    )

@app.route('/download_data')
def download_data():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']
    # Puxa todas as colunas salvas no banco para esse RE
    conn = sqlite3.connect(DB_PATH_TEMPLATE.format(atividade='A'))
    df = pd.read_sql_query("SELECT * FROM results WHERE re = ?", conn, params=(re_val,))
    conn.close()
    # Exporta para Excel
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        download_name=f'dados_coletados_{re_val}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

