from flask import Flask, render_template, redirect, url_for, jsonify, request, session, flash, send_file
from services.login_service import iniciar_navegador, efetuar_login
from services.orquestracao_service import orquestrar_tarefas
from utils.db import get_student, save_result, init_db
from models.tarefa import Tarefa
import sqlite3
import pandas as pd
from config.settings import INSTRUTOR_USERNAME, INSTRUTOR_PASSWORD
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
from datetime import datetime
import pytz


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
    '8': ('CFS25', 'Atividade Prática CFS2025'),      
}

def check_auth(username, password):
    return username == INSTRUTOR_USERNAME and password == INSTRUTOR_PASSWORD

def authenticate():
    return Response(
        'Acesso restrito. Forneça usuário e senha.', 401,
        {'WWW-Authenticate': 'Basic realm="Área do Instrutor"'}
    )

def aluno_esta_logado(re_val):
    try:
        with open(LOGADOS_ARQUIVO, 'r') as f:
            logados = json.load(f)  
        return logados.get(re_val, False) 
    except:
        return False  


ESTADO_ARQUIVO = 'atividades_estado.json'
def carregar_estado_atividades():
    try:
        with open(ESTADO_ARQUIVO, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {sigla: True for _, (sigla, _) in ATIVIDADES_OPCOES.items()}

def salvar_estado_atividades(estado):
    with open(ESTADO_ARQUIVO, 'w') as f:
        json.dump(estado, f)

@app.route('/gerenciar_atividades', methods=['POST'])
def gerenciar_atividades():
    estado = carregar_estado_atividades()
    
    sigla = request.form.get('sigla')
    novo_estado = request.form.get('estado') == 'on'
    estado[sigla] = novo_estado
    salvar_estado_atividades(estado)

    return redirect(url_for('instrutor'))


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

    estado = carregar_estado_atividades()
    atividades = [(sigla, nome, estado.get(sigla, False)) for _, (sigla, nome) in ATIVIDADES_OPCOES.items()]
    alunos_logados = contar_logados()
    
    return render_template('instrutor.html', atividades=atividades, alunos_logados=alunos_logados)

@app.route('/gerar_relatorio', methods=['POST'])
def gerar_relatorio():
    try:
        protocolos = session.get('protocolos_filtrados')

        if not protocolos:
            return "Nenhuma consulta foi feita anteriormente.", 400

        conn = sqlite3.connect(DB_PATH)
        placeholders = ','.join(['?'] * len(protocolos))
        query = f"SELECT * FROM results WHERE protocolo IN ({placeholders})"
        df = pd.read_sql_query(query, conn, params=protocolos)
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
    
    except Exception as e:
        return f"Erro interno: {str(e)}", 500

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
            session['nome'], session['pelotao'], session['curso'] = student
            registrar_login_aluno(re_val) 
            return redirect(url_for('analyze'))
        else:
            flash('RE não encontrado.', 'error')
    return render_template('login.html')


from flask import (
    Blueprint, render_template, request, session, redirect,
    url_for, flash, Response, stream_with_context
)

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if 're' not in session:
        return redirect(url_for('login'))
    
    estado = carregar_estado_atividades()
    atividades_ativas = {
        chave: (sigla, nome)
        for chave, (sigla, nome) in ATIVIDADES_OPCOES.items()
        if estado.get(sigla, False)
    }

    if request.method == 'GET':
        return render_template('analyze.html',
                               options=atividades_ativas,
                               re=session['re'])

    protocolo = request.form.get('protocolo','').strip()
    if not protocolo:
        flash('Protocolo é obrigatório.', 'error')
        return render_template('analyze.html',
                               options=atividades_ativas,
                               re=session['re'])

    sigla_atividade = request.form.get('atividade')
    chave_correspondente = next(
        (chave for chave, (sigla, _) in atividades_ativas.items() if sigla == sigla_atividade),
        None
    )
    if not chave_correspondente:
        flash('Selecione uma atividade válida.', 'error')
        return render_template('analyze.html',
                            options=atividades_ativas,
                            re=session['re'])
    tipos = [sigla_atividade]


    tarefa = Tarefa(
        protocolo=protocolo,
        re=session['re'],
        nome=session['nome'],
        pelotao=session['pelotao'],
        curso=session.get('curso', ''),
        atividades=tipos
    )

    def generate():        
        yield render_template('analyze_stream_header.html',
                              options=ATIVIDADES_OPCOES,
                              re=session['re'])        
        yield "<script>appendLog('Iniciando navegador do SISEG Treinamento');</script>"
        driver = iniciar_navegador(headless=True) 
        yield "<script>appendLog('Efetuando login no SISEG');</script>"
        efetuar_login(driver)
        yield "<script>appendLog('Login efetuado com sucesso.');</script>"
        yield "<script>appendLog('Iniciando coleta de dados da ocorrência no SISEG');</script>"
        yield "<script>mostrarCarregando();</script>"
        resultados = orquestrar_tarefas(driver, tarefa)
        for tipo, resultado in zip(tipos, resultados):
            save_result(tipo, resultado)
            yield f"<script>appendLog('Resultado {tipo}: {resultado}');</script>"
        driver.quit()
        yield "<script>appendLog('Processo concluído.');</script>"
        yield "<script>appendLog('Processo concluído.');</script>"        
        target = url_for('report')   
        yield f"<script>setTimeout(()=>window.location.href='{target}', 500);</script>"       
        yield "</body></html>"
    return Response(
        stream_with_context(generate()),
        mimetype='text/html',
        headers={
            'Cache-Control':   'no-cache',
            'X-Accel-Buffering': 'no'      
        }
    )
    
  # Uso no PC Windons
# @app.route('/analyze', methods=['GET', 'POST'])
# def analyze():
#     re_val = session.get('re')    
#     if not re_val or not aluno_esta_logado(re_val):
#         session.clear()  
#         return redirect(url_for('login'))   
    
#     if 're' not in session:
#         return redirect(url_for('login'))    

#     estado = carregar_estado_atividades()
#     atividades_ativas = {
#         chave: (sigla, nome)
#         for chave, (sigla, nome) in ATIVIDADES_OPCOES.items()
#         if estado.get(sigla, False)
#     }
    
#     if request.method == 'GET':
#         return render_template('analyze.html',
#                                options=atividades_ativas,
#                                re=session.get('re'))
   
#     re_val = request.form.get('re', session['re']).strip()
#     protocolo = request.form.get('protocolo', '').strip()
#     if not protocolo:
#         flash('Protocolo é obrigatório.', 'error')
#         return render_template('analyze.html',
#                                options=atividades_ativas,
#                                re=session['re'])
    
#     sigla_atividade = request.form.get('atividade')
#     chave_correspondente = next(
#         (chave for chave, (sigla, _) in atividades_ativas.items() if sigla == sigla_atividade),
#         None
#     )
#     if not chave_correspondente:
#         flash('Selecione uma atividade válida.', 'error')
#         return render_template('analyze.html',
#                             options=atividades_ativas,
#                             re=session['re'])
#     tipos = [sigla_atividade]    
    
#     print(f"DEBUG analyze: tipos = {tipos!r}")    

#     driver = iniciar_navegador(headless=False) #False para habilitar verificação do navegador
#     efetuar_login(driver)
#     tarefa = Tarefa(
#         protocolo=protocolo,
#         re=session['re'],
#         nome=session['nome'],
#         pelotao=session['pelotao'],
#         curso=session.get('curso', ''),
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
        "SELECT atividade, protocolo, erros_avaliacao, nota, curso FROM results WHERE re = ?",
        conn, params=(re_val,)
    )
    conn.close()
    df['status'] = df['nota'].map({1: 'certo', 0: 'errado'})
    data = df[['atividade','protocolo','status','erros_avaliacao', 'curso']]\
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
    re_val = session.get('re')
    if re_val:
        remover_login_aluno(re_val) 
    session.clear()
    return redirect(url_for('login'))


@app.route('/consultar_relatorio', methods=['POST'])
def consultar_relatorio():
    pelotao = request.form.get('pelotao')
    atividade = request.form.get('atividade')
    matricula = request.form.get('matricula')
    curso = request.form.get('curso')

    query = "SELECT rowid, nome, curso, atividade, protocolo, erros_avaliacao, nota FROM results WHERE 1=1"
    params = []

    if pelotao:
        query += " AND pelotao = ?"
        params.append(pelotao)
    if atividade:
        query += " AND atividade = ?"
        params.append(atividade)
    if matricula:
        query += " AND re = ?"
        params.append(matricula)
    if curso:
        query += " AND curso = ?"       
        params.append(curso)

    query += " ORDER BY rowid DESC"

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    df['status'] = df['nota'].map({1: 'certo', 0: 'errado'})
    data = df[['rowid', 'nome', 'curso', 'atividade', 'protocolo', 'status', 'erros_avaliacao']].to_dict(orient='records')
   
    session['protocolos_filtrados'] = df['protocolo'].tolist()

    return render_template('resultado_instrutor.html', data=data)



@app.route('/ultimos_registros')
def ultimos_registros():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT nome, pelotao, atividade, protocolo, nota, timestamp FROM results ORDER BY ROWID DESC LIMIT 10",
        conn
    )
    conn.close()

    df['nome'] = df['nome'].str.upper()
    df['status'] = df['nota'].map({1: 'certo', 0: 'errado'})
    
    fuso_porto_velho = pytz.timezone("America/Porto_Velho")
    def formatar_data(data_str):
        try:            
            dt_utc = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)           
            dt_local = dt_utc.astimezone(fuso_porto_velho)            
            return dt_local.strftime("%d/%m/%Y %H:%M:%S")
        except:
            return "??/??/???? ??:??:??"
    df['data_formatada'] = df['timestamp'].apply(formatar_data)

    data = df[['nome', 'pelotao', 'atividade', 'data_formatada', 'protocolo', 'status']].to_dict(orient='records')

    return render_template('partials/ultimos_registros.html', data=data)



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


LOGADOS_ARQUIVO = 'usuarios_logados.json'
def registrar_login_aluno(re_val):
    try:
        with open(LOGADOS_ARQUIVO, 'r') as f:
            logados = json.load(f)
    except FileNotFoundError:
        logados = {}

    logados[re_val] = True
    with open(LOGADOS_ARQUIVO, 'w') as f:
        json.dump(logados, f)

def limpar_logins_alunos():
    with open(LOGADOS_ARQUIVO, 'w') as f:
        json.dump({}, f)

def contar_logados():
    try:
        with open(LOGADOS_ARQUIVO, 'r') as f:
            logados = json.load(f)
        return len(logados)
    except:
        return 0
    
def remover_login_aluno(re_val):
    try:
        with open(LOGADOS_ARQUIVO, 'r') as f:
            logados = json.load(f)
    except FileNotFoundError:
        logados = {}

    if re_val in logados:
        del logados[re_val]

    with open(LOGADOS_ARQUIVO, 'w') as f:
        json.dump(logados, f)

@app.route('/logout_todos_alunos', methods=['POST'])
def logout_todos_alunos():
    if not session.get('instrutor'):
        return redirect(url_for('login_instrutor'))

    limpar_logins_alunos()
    flash("Todas as sessões de alunos foram encerradas.", "info")
    return redirect(url_for('instrutor'))

@app.route('/grafico_dados')
def grafico_dados():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")
    pelotao = request.args.get("pelotao")
    atividade = request.args.get("atividade")
    status = request.args.get("status")  
    curso = request.args.get("curso")

    query = "SELECT atividade, pelotao, nota FROM results WHERE 1=1"
    params = []

    if inicio:
        query += " AND DATE(timestamp) >= ?"
        params.append(inicio)
    if fim:
        query += " AND DATE(timestamp) <= ?"
        params.append(fim)
    if pelotao and pelotao != "todos":
        query += " AND pelotao = ?"
        params.append(pelotao)
    if atividade and atividade != "todas":
        query += " AND atividade = ?"
        params.append(atividade)
    if status and status != "todos":
        query += " AND nota = ?"
        params.append(1 if status == "certo" else 0)   
    if curso and curso != "todos":  
        query += " AND curso = ?"
        params.append(curso) 

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        print("RESULTADO:", df.head())
    except Exception as e:
        print("[ERRO NA QUERY]", e)
        return jsonify({"erro": str(e)}), 500

    if df.empty:
        return jsonify([])

    df['resultado'] = df['nota'].map({1: 'Certo', 0: 'Errado'})
    dados = df.groupby(['atividade', 'resultado']).size().unstack(fill_value=0).reset_index()
    return jsonify(dados.to_dict(orient='records'))


@app.route('/grafico_full')
def grafico_full():
    return render_template('grafico_full.html')


if __name__ == '__main__':
    app.run(debug=True)

