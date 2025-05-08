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
from config.settings import DB_PATH
from flask import Response, stream_with_context, render_template
import json
from flask import Flask, render_template, request, flash
from utils.db import init_db, get_student
from flask import Flask, request, Response, render_template, redirect, url_for, flash, send_file
from flask import flash, redirect, url_for, current_app
from selenium.common.exceptions import InvalidSessionIdException

app = Flask(__name__)
app.secret_key = 'troque_para_uma_chave_secreta_segura'

ATIVIDADES_OPCOES = {
    '1': ('A', 'Atividade A'),
    '2': ('B', 'Atividade B'),
    '3': ('C', 'Atividade C'),
    '4': ('D', 'Atividade D'),
    '5': ('E', 'Atividade E'),
    '6': ('F', 'Atividade F'),
    '7': ('PPE', 'Prova Prática de Execução'),   
    
}

INSTRUTOR_USERNAME = 'dinfo'
INSTRUTOR_PASSWORD = 'dinfo2025'

def check_auth(username, password):
    return username == INSTRUTOR_USERNAME and password == INSTRUTOR_PASSWORD

def authenticate():
    return Response(
        'Acesso restrito. Forneça usuário e senha.', 401,
        {'WWW-Authenticate': 'Basic realm="Área do Instrutor"'}
    )
@app.route('/login_instrutor', methods=['GET', 'POST'])
def login_instrutor():
    if request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')

        if username == INSTRUTOR_USERNAME and password == INSTRUTOR_PASSWORD:
            session['instrutor'] = True
            return redirect(url_for('instrutor'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
            return redirect(url_for('login_instrutor'))

    return render_template('login_instrutor.html')

@app.route('/logout_instrutor')
def logout_instrutor():
    session.pop('instrutor', None)
    return redirect(url_for('login'))

@app.route('/instrutor')
def instrutor():
    if not session.get('instrutor'):
        return redirect(url_for('login_instrutor'))
    return render_template('instrutor.html')

@app.route('/gerar_relatorio', methods=['POST'])
def gerar_relatorio():
    pelotao = request.form.get('pelotao')
    atividade = request.form.get('atividade')
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM results WHERE 1=1"

    if pelotao:
        query += f" AND pelotao = '{pelotao}'"
    if atividade:
        query += f" AND atividade = '{atividade}'"

    df = pd.read_sql_query(query, conn)
    conn.close()

    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatório')

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_instrutor.xlsx'
    )

@app.before_request
def setup_db():
    init_db()

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        re_val = request.form.get('re', '').strip()
        student = get_student(re_val)
        if student:
            session['re'] = re_val
            session['nome'], session['pelotao'] = student
            return redirect(url_for('analyze'))
        else:
            flash('RE não encontrado.', 'error')
    return render_template('login.html')


## Usado Somente para VM
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    print("[analyze] entrada na rota /analyze")
    if 're' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('analyze.html',
                               options=ATIVIDADES_OPCOES,
                               re=session.get('re'))

    protocolo = request.form.get('protocolo', '').strip()
    if not protocolo:
        flash('Protocolo é obrigatório.', 'error')
        return render_template('analyze.html',
                               options=ATIVIDADES_OPCOES,
                               re=session['re'])

    escolha = request.form.get('atividade')
    print(f"[analyze] atividade escolhida = {escolha!r}")
    if not escolha or escolha not in ATIVIDADES_OPCOES:
        flash('Selecione uma atividade válida.', 'error')
        return render_template('analyze.html',
                               options=ATIVIDADES_OPCOES,
                               re=session['re'])

    tipos = [ATIVIDADES_OPCOES[escolha][0]]
    tarefa = Tarefa(
        protocolo=protocolo,
        re=session['re'],
        nome=session['nome'],
        pelotao=session['pelotao'],
        atividades=tipos
    )

    def generate():
        # HTML wrapper para browser renderizar em tempo real
        yield '<!DOCTYPE html><html><body><pre>'
        yield 'Iniciando navegador headless...\n'
        driver = iniciar_navegador(headless=True)
        yield 'Driver iniciado com sucesso.\n\n'

        yield 'Efetuando login...\n'
        efetuar_login(driver)
        yield 'Login efetuado com sucesso.\n\n'

        yield 'Orquestrando tarefas...\n'
        resultados = orquestrar_tarefas(driver, tarefa)
        for tipo, resultado in zip(tipos, resultados):
            save_result(tipo, resultado)
            yield f'Resultado {tipo}: {resultado}\n'

        driver.quit()
        yield '\nProcesso concluído.\n'
        # Fecha tags HTML
        yield '</pre></body></html>'

    return Response(stream_with_context(generate()), mimetype='text/html')

# @app.route('/analyze', methods=['GET', 'POST'])
# def analyze():
#     if 're' not in session:
#         return redirect(url_for('login'))
    
#     if request.method == 'GET':
#         return render_template('analyze.html',
#                                options=ATIVIDADES_OPCOES,
#                                re=session.get('re'))
   
#     re_val = request.form.get('re', session['re']).strip()
#     protocolo = request.form.get('protocolo', '').strip()
#     if not protocolo:
#         flash('Protocolo é obrigatório.', 'error')
#         return render_template('analyze.html',
#                                options=ATIVIDADES_OPCOES,
#                                re=session['re'])
    
#     escolha = request.form.get('atividade')
#     if not escolha or escolha not in ATIVIDADES_OPCOES:
#         flash('Selecione uma atividade válida.', 'error')
#         return render_template('analyze.html',
#                             options=ATIVIDADES_OPCOES,
#                             re=session['re'])

#     tipos = [ATIVIDADES_OPCOES[escolha][0]]    
    
#     print(f"DEBUG analyze: tipos = {tipos!r}")    

#     driver = iniciar_navegador(headless=False) #False para habilitar verificação do navegador
#     efetuar_login(driver)
#     tarefa = Tarefa(
#         protocolo=protocolo,
#         re=session['re'],
#         nome=session['nome'],
#         pelotao=session['pelotao'],
#         atividades=tipos        
#     )
#     print("DEBUG analyze: chamando orquestrar_tarefas")

#     resultados = orquestrar_tarefas(driver, tarefa)
#     for tipo, resultado in zip(tipos, resultados):
#         save_result(tipo, resultado)
#     driver.quit()

    
#     return render_template(
#         'result.html',
#         resultados=zip(tipos, resultados)   
#     )

@app.route('/report')
def report():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']   
    conn = sqlite3.connect(DB_PATH)    
    df = pd.read_sql_query(
        "SELECT atividade, protocolo, erros_avaliacao, nota FROM results WHERE re = ?",
        conn, params=(re_val,)
    )
    conn.close()
    df['status'] = df['nota'].map({1: 'certo', 0: 'errado'})
    data = df[['atividade','protocolo','status','erros_avaliacao']]\
             .to_dict(orient='records')

    return render_template('report.html', data=data, re=re_val)


@app.route('/download_excel')
def download_excel():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM results WHERE re = ?", conn, params=(re_val,))
    conn.close()    
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        download_name=f'dados_coletados_{re_val}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/quesitos')
def quesitos():   
    return render_template('quesitos.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(ValueError)
def handle_value_error(e):
    current_app.logger.error(f"ValueError não capturada: {e}")
    flash(
        "A sessão do navegador foi perdida durante a execução. "
        "Por favor, recarregue a página e tente novamente."
        "Verifique se o número do protocolo está correto e que esteja devidamente finalizado no ambinete SISEG",
        'error'
    )
    return redirect(url_for('analyze'))

@app.errorhandler(InvalidSessionIdException)
def handle_invalid_session(e):
    current_app.logger.error(f"InvalidSessionIdException capturada: {e}")
    flash(
        "A sessão do navegador foi perdida durante a execução. "
        "Por favor, recarregue a página e tente novamente."
        "Verifique se o número do protocolo está correto e que esteja devidamente finalizado no ambinete SISEG",
        'error'
    )
    return redirect(url_for('analyze'))

if __name__ == '__main__':
    app.run(debug=True)

