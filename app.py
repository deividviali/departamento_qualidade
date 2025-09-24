from flask import Flask, render_template, redirect, url_for, jsonify, request, session, flash, send_file
from services.login_service import iniciar_navegador, efetuar_login
from services.orquestracao_service import orquestrar_tarefas
from utils.db import get_student, save_result
from models.tarefa import Tarefa
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import Response, stream_with_context, render_template
import json
from flask import Flask, render_template, request, flash
from utils.db import get_student, save_result, get_db_connection
from flask import Flask, request, Response, render_template, redirect, url_for, flash, send_file
from flask import flash, redirect, url_for, current_app
from selenium.common.exceptions import InvalidSessionIdException
from datetime import datetime
from sqlalchemy import text
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from io import StringIO
import secrets
from utils.db import engine_main, engine_extern
from services.cadastro_efetivo_producao import atualizar_efetivo
from services.login_service_producao_siseg import login_siseg

# import os
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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


def authenticate():
    return Response(
        'Acesso restrito. Forneça usuário e senha.', 401,
        {'WWW-Authenticate': 'Basic realm="Área do Instrutor"'}
    )

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

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        re_val = request.form.get('re', '').strip()
        if not re_val:
            flash("RE é obrigatório.", "error")
            return render_template('login.html')

        try:
            engine = get_db_connection()
            with engine.connect() as conn:
                aluno = conn.execute(
                    text("SELECT nome, pelotao, curso FROM students WHERE re = :re"),
                    {"re": re_val}
                ).fetchone()

            if aluno:
                session.update({
                    "re": re_val,
                    "nome": aluno.nome,
                    "pelotao": aluno.pelotao,
                    "curso": aluno.curso
                })

                # 🔹 Sessão + Auditoria
                registrar_sessao(
                    user_type="aluno",
                    user_id=re_val,
                    nome=aluno.nome,
                    ip=request.remote_addr,
                    user_agent=request.headers.get("User-Agent")
                )
                registrar_auditoria("Login", f"Aluno {re_val} logou")

                return redirect(url_for('analyze'))

            flash("RE não encontrado.", "error")

        except Exception as e:
            flash(f"Erro no login: {str(e)}", "error")

    return render_template('login.html')

@app.route('/login_instrutor', methods=['GET', 'POST'])
def login_instrutor():
    if request.method == 'POST':
        matricula = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '').strip()

        try:
            engine = get_db_connection()
            with engine.connect() as conn:
                user = conn.execute(
                    text("SELECT * FROM usuario_sistema WHERE matricula = :mat"),
                    {"mat": matricula}
                ).fetchone()

                if user and check_password_hash(user.senha, senha):
                    # 🔹 Sessão Flask
                    session["usuario"] = user.nome_guerra
                    session["user_type"] = "sistema"
                    session["user_id"] = user.matricula

                    # 🔹 Buscar perfis do usuário
                    perfis = conn.execute(text("""
                        SELECT p.nome
                        FROM usuario_perfis up
                        JOIN perfis p ON up.perfil_id = p.id
                        WHERE up.matricula = :mat
                    """), {"mat": matricula}).fetchall()
                    perfis = [p.nome for p in perfis]

                    if not perfis:
                        flash("Usuário sem perfis atribuídos.", "error")
                        return redirect(url_for("login_instrutor"))

                    # 🔹 Sessão + Auditoria no Banco
                    registrar_sessao(
                        user_type="sistema",
                        user_id=user.matricula,      # Matrícula = RE
                        nome=user.nome_guerra,       # Nome de Guerra
                        ip=request.remote_addr,
                        user_agent=request.headers.get("User-Agent")
                    )
                    registrar_auditoria(
                        acao="Login",
                        detalhes=f"Usuário {user.matricula} logou",
                        user_id=user.matricula,
                        nome=user.nome_guerra,
                        user_type="sistema"
                    )

                    # 🔹 Redirecionamento pelo perfil
                    if len(perfis) == 1:
                        session["perfil"] = perfis[0]
                        if perfis[0] == "CURSOS":
                            return redirect(url_for("instrutor"))
                        elif perfis[0] == "SUPORTE":
                            return redirect(url_for("suporte"))
                        elif perfis[0] == "ADMIN":
                            return redirect(url_for("admin.index"))
                    else:
                        return render_template("selecionar_perfil.html", perfis=perfis)

                # ❌ Login inválido
                flash("Matrícula ou senha inválidos.", "error")
                return redirect(url_for("login_instrutor"))

        except Exception as e:
            flash(f"Erro no login: {str(e)}", "error")
            return redirect(url_for("login_instrutor"))

    return render_template('login_instrutor.html')


@app.route('/escolher_perfil', methods=['POST'])
def escolher_perfil():
    perfil = request.form.get('perfil')
    session['perfil'] = perfil

    

    if perfil == "CURSOS":
        return redirect(url_for('instrutor'))
    elif perfil == "SUPORTE":
        return redirect(url_for('suporte'))
    elif perfil == "ADMIN":
        return redirect(url_for('admin.index'))

    flash("Perfil inválido!", "error")
    return redirect(url_for('login_instrutor'))

@app.route('/logout_instrutor')
def logout_instrutor():
    if "usuario" in session:
        registrar_auditoria("Logout", f"Usuário Sistema {session.get('usuario')} saiu")
    encerrar_sessao()
    return redirect(url_for('login'))

@app.route('/suporte')
def suporte():
    if session.get('perfil') != 'SUPORTE':
        return redirect(url_for('login_instrutor'))

    # 🔹 Auditoria de acesso
    registrar_auditoria(
        acao="Acesso",
        detalhes=f"Usuário {session.get('user_id')} acessou a tela de SUPORTE",
        user_id=session.get('user_id'),
        nome=session.get('usuario'),
        user_type="sistema"
    )

    return render_template('suporte.html')

@app.route('/instrutor')
def instrutor():
    if session.get('perfil') != 'CURSOS':
        return redirect(url_for('login_instrutor'))

    estado = carregar_estado_atividades()
    atividades = [(sigla, nome, estado.get(sigla, False)) for _, (sigla, nome) in ATIVIDADES_OPCOES.items()]   
    return render_template('instrutor.html', atividades=atividades,)


@app.route('/gerar_relatorio', methods=['POST'])
def gerar_relatorio():
    try:
        protocolos = session.get('protocolos_filtrados')

        if not protocolos:
            return "Nenhuma consulta foi feita anteriormente.", 400

        engine = get_db_connection()

        placeholders = ", ".join(["%s"] * len(protocolos))
        query = f"SELECT * FROM results WHERE protocolo IN ({placeholders})"

        df = pd.read_sql_query(query, engine, params=tuple(protocolos))

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
    
# Rota para VM Linux
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    re_val = session.get("re")
    if not re_val:
        session.clear()
        return redirect(url_for("login"))

    # 🔹 Verificação de sessão ativa no banco
    engine = get_db_connection()
    with engine.connect() as conn:
        ativo = conn.execute(
            text("SELECT COUNT(*) FROM user_sessions WHERE user_id = :re AND ativo = 1"),
            {"re": re_val}
        ).scalar()

    if ativo == 0:
        session.clear()
        return redirect(url_for("login"))

    registrar_auditoria("Acesso", f"Aluno {re_val} acessou a tela inicial de seleção de atividades")

    # 🔹 Estado das atividades
    estado = carregar_estado_atividades()
    atividades_ativas = {
        chave: (sigla, nome)
        for chave, (sigla, nome) in ATIVIDADES_OPCOES.items()
        if estado.get(sigla, False)
    }

    # Primeira entrada (GET)
    if request.method == 'GET':
        return render_template('analyze.html',
                               options=atividades_ativas,
                               re=re_val)

    # Envio do formulário (POST)
    protocolo = request.form.get('protocolo', '').strip()
    if not protocolo:
        flash('Protocolo é obrigatório.', 'error')
        return render_template('analyze.html',
                               options=atividades_ativas,
                               re=re_val)

    sigla_atividade = request.form.get('atividade')
    chave_correspondente = next(
        (chave for chave, (sigla, _) in atividades_ativas.items() if sigla == sigla_atividade),
        None
    )
    if not chave_correspondente:
        flash('Selecione uma atividade válida.', 'error')
        return render_template('analyze.html',
                               options=atividades_ativas,
                               re=re_val)

    tipos = [sigla_atividade]

    tarefa = Tarefa(
        protocolo=protocolo,
        re=re_val,
        nome=session['nome'],
        pelotao=session['pelotao'],
        curso=session.get('curso', ''),
        atividades=tipos
    )

    def generate():
        # Cabeçalho de streaming
        yield render_template('analyze_stream_header.html',
                              options=ATIVIDADES_OPCOES,
                              re=re_val)

        yield "<script>appendLog('Iniciando navegador do SISEG');</script>"
        driver = iniciar_navegador(headless=True)  # 🔹 headless=True para VM Linux
        yield "<script>appendLog('Efetuando login no SISEG...');</script>"
        efetuar_login(driver)
        yield "<script>appendLog('Login efetuado com sucesso.');</script>"

        yield "<script>appendLog('Iniciando coleta de dados...');</script>"
        yield "<script>mostrarCarregando();</script>"
        resultados = orquestrar_tarefas(driver, tarefa)

        for tipo, resultado in zip(tipos, resultados):
            save_result(tipo, resultado)
            yield f"<script>appendLog('Resultado {tipo}: {resultado}');</script>"

        driver.quit()
        yield "<script>appendLog('Processo concluído.');</script>"
        target = url_for('report')
        yield f"<script>setTimeout(()=>window.location.href='{target}', 500);</script>"
        yield "</body></html>"

    return Response(
        stream_with_context(generate()),
        mimetype='text/html',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

    
  # Uso no PC Windons
# @app.route('/analyze', methods=['GET', 'POST'])
# def analyze():
#     re_val = session.get("re")  # 🔹 garante que existe valor
#     if not re_val:
#         session.clear()
#         return redirect(url_for("login"))

#     engine = get_db_connection()
#     with engine.connect() as conn:
#         ativo = conn.execute(
#             text("SELECT COUNT(*) FROM user_sessions WHERE user_id = :re AND ativo = 1"),
#             {"re": re_val}
#         ).scalar()

#     if ativo == 0:
#         session.clear()
#         return redirect(url_for("login"))

#     registrar_auditoria("Acesso", f"Aluno {re_val} acessou a tela inicial de seleção de atividades")

#     # 🔹 Estado das atividades
#     estado = carregar_estado_atividades()
#     atividades_ativas = {
#         chave: (sigla, nome)
#         for chave, (sigla, nome) in ATIVIDADES_OPCOES.items()
#         if estado.get(sigla, False)
#     }

#     # 🔹 Primeira vez que entra (tela inicial)
#     if request.method == 'GET':
#         return render_template('analyze.html',
#                                options=atividades_ativas,
#                                re=re_val)

#     # 🔹 Quando envia o formulário
#     protocolo = request.form.get('protocolo', '').strip()
#     if not protocolo:
#         flash('Protocolo é obrigatório.', 'error')
#         return render_template('analyze.html',
#                                options=atividades_ativas,
#                                re=re_val)

#     sigla_atividade = request.form.get('atividade')
#     chave_correspondente = next(
#         (chave for chave, (sigla, _) in atividades_ativas.items() if sigla == sigla_atividade),
#         None
#     )
#     if not chave_correspondente:
#         flash('Selecione uma atividade válida.', 'error')
#         return render_template('analyze.html',
#                                options=atividades_ativas,
#                                re=re_val)

#     tipos = [sigla_atividade]
#     print(f"DEBUG analyze: tipos = {tipos!r}")

#     driver = iniciar_navegador(headless=False)  # False para visualizar
#     efetuar_login(driver)

#     tarefa = Tarefa(
#         protocolo=protocolo,
#         re=re_val,
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
    

    engine = get_db_connection()
    query = """
        SELECT atividade, protocolo, erros_avaliacao, nota, curso
        FROM results
        WHERE re = :re
    """
    df = pd.read_sql_query(text(query), engine, params={"re": re_val})

    df['status'] = df['nota'].map({1: 'certo', 0: 'errado', 'certo': 'certo', 'errado': 'errado'}).fillna('pendente')
    data = df[['atividade', 'protocolo', 'status', 'erros_avaliacao', 'curso']].to_dict(orient='records')

    return render_template('report.html', data=data, re=re_val)

@app.route('/download_excel')
def download_excel():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']

    engine = get_db_connection()
    query = "SELECT protocolo, nota, erros_avaliacao FROM results WHERE re = :re"
    df = pd.read_sql_query(text(query), engine, params={"re": re_val})

    df['status'] = df['nota'].map({1: 'certo', 0: 'errado', 'certo': 'certo', 'errado': 'errado'}).fillna('pendente')

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name=f"relatorio_{re_val}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
@app.route('/download_pdf')
def download_pdf():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']

    engine = get_db_connection()
    query = "SELECT protocolo, nota, erros_avaliacao FROM results WHERE re = :re"
    df = pd.read_sql_query(text(query), engine, params={"re": re_val})

    df['status'] = df['nota'].map({1: 'certo', 0: 'errado', 'certo': 'certo', 'errado': 'errado'}).fillna('pendente')

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
        mimetype="application/pdf"
    )

@app.route('/download_data')
def download_data():
    if 're' not in session:
        return redirect(url_for('login'))
    re_val = session['re']

    engine = get_db_connection()
    query = "SELECT * FROM results WHERE re = :re"
    df = pd.read_sql_query(text(query), engine, params={"re": re_val})

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name=f"dados_coletados_{re_val}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/quesitos')
def quesitos():   
    return render_template('quesitos.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    re_val = session.get('re')
    if re_val:
        registrar_auditoria("Logout", f"Aluno {re_val} saiu")
    encerrar_sessao()
    return redirect(url_for('login'))

@app.route('/consultar_relatorio', methods=['POST'])
def consultar_relatorio():
    pelotao = request.form.get('pelotao')
    atividade = request.form.get('atividade')
    matricula = request.form.get('matricula')
    curso = request.form.get('curso')

    query = """
        SELECT id, nome, curso, atividade, protocolo, erros_avaliacao, nota, timestamp
        FROM results
        WHERE 1=1
    """
    params = {}

    if pelotao:
        query += " AND pelotao = :pelotao"
        params["pelotao"] = pelotao
    if atividade:
        query += " AND atividade = :atividade"
        params["atividade"] = atividade
    if matricula:
        query += " AND re = :matricula"
        params["matricula"] = matricula
    if curso:
        query += " AND curso = :curso"
        params["curso"] = curso

    query += " ORDER BY timestamp DESC"

    engine = get_db_connection()
    df = pd.read_sql_query(text(query), engine, params=params)

    df['status'] = df['nota'].map({1: 'certo', 0: 'errado', 'certo': 'certo', 'errado': 'errado'}).fillna('pendente')
    data = df[['id','nome', 'curso', 'atividade', 'protocolo', 'status', 'erros_avaliacao', 'timestamp']].to_dict(orient='records')

    session['protocolos_filtrados'] = df['protocolo'].tolist()

    return render_template('resultado_instrutor.html', data=data)

@app.route('/ultimos_registros')
def ultimos_registros():
    engine = get_db_connection()
    query = """
        SELECT nome, pelotao, atividade, protocolo, nota, timestamp
        FROM results
        ORDER BY timestamp DESC
        LIMIT 10
    """
    df = pd.read_sql_query(text(query), engine)

    df['nome'] = df['nome'].str.upper()
    df['status'] = df['nota'].map({1: 'certo', 0: 'errado', 'certo': 'certo', 'errado': 'errado'}).fillna('pendente')

    def formatar_data(data_val):
        try:
            if isinstance(data_val, datetime):
                return data_val.strftime("%d/%m/%Y %H:%M:%S")
            else:
                return datetime.strptime(str(data_val), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        except Exception as e:
            print("Erro formatando data:", data_val, e)
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
        query += " AND DATE(timestamp) >= %s"
        params.append(inicio)
    if fim:
        query += " AND DATE(timestamp) <= %s"
        params.append(fim)
    if pelotao and pelotao != "todos":
        query += " AND pelotao = %s"
        params.append(pelotao)
    if atividade and atividade != "todas":
        query += " AND atividade = %s"
        params.append(atividade)
    if status and status != "todos":
        query += " AND nota = %s"
        params.append(1 if status == "certo" else 0)
    if curso and curso != "todos":
        query += " AND curso = %s"
        params.append(curso)

    try:
        engine = get_db_connection()
        df = pd.read_sql_query(query, engine, params=tuple(params))
        if df.empty:
            return jsonify([])

        df['resultado'] = df['nota'].map({1: 'Certo', 0: 'Errado'})
        dados = df.groupby(['atividade', 'resultado']).size().unstack(fill_value=0).reset_index()

        return jsonify(dados.to_dict(orient='records'))

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/grafico_full')
def grafico_full():
    return render_template('grafico_full.html')

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
# 🔐 Tela inicial de gerenciamento
@admin_bp.route("/")
def index():
    if session.get("perfil") != "ADMIN":
        flash("Acesso restrito", "error")
        return redirect(url_for("login_instrutor"))    
    
    engine = get_db_connection()
    with engine.connect() as conn:
        total_online = conn.execute(
            text("SELECT COUNT(*) FROM user_sessions WHERE ativo = 1")
        ).scalar()

    return render_template("admin/index.html", total_online=total_online)

# ➕ Criar novo usuário sistema
@admin_bp.route("/create", methods=["GET", "POST"])
def create_user():
    if session.get("perfil") != "ADMIN":
        flash("Acesso restrito", "error")
        return redirect(url_for("login_instrutor"))

    if request.method == "POST":
        matricula = request.form["matricula"]
        nome = request.form["nome"]
        nome_guerra = request.form["nome_guerra"]
        email = request.form["email"]              
        senha = request.form["senha"]

        senha_hash = generate_password_hash(senha)

        engine = get_db_connection()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO usuario_sistema (matricula, nome, nome_guerra, email, senha)
                    VALUES (:matricula, :nome, :nome_guerra, :email, :senha)
                """),
                {
                    "matricula": matricula,
                    "nome": nome,
                    "nome_guerra": nome_guerra,
                    "email": email,
                    "senha": senha_hash
                }
            )

        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for("admin.index"))
    return render_template("admin/create.html")

# ✏️ Editar senha ou nome uuário sistema
@admin_bp.route("/edit/<matricula>", methods=["GET", "POST"])
def edit_user(matricula):
    engine = get_db_connection()
    if request.method == "POST":
        nome = request.form["nome"]
        nome_guerra = request.form["nome_guerra"]
        email = request.form["email"]
        senha = request.form.get("senha")

        with engine.begin() as conn:
            if senha:
                senha_hash = generate_password_hash(senha)
                conn.execute(
                    text("""
                        UPDATE usuario_sistema 
                        SET nome=:nome, nome_guerra=:nome_guerra, email=:email, senha=:senha 
                        WHERE matricula=:matricula
                    """),
                    {"nome": nome, "nome_guerra": nome_guerra, "email": email,
                     "senha": senha_hash, "matricula": matricula}
                )
            else:
                conn.execute(
                    text("""
                        UPDATE usuario_sistema 
                        SET nome=:nome, nome_guerra=:nome_guerra, email=:email
                        WHERE matricula=:matricula
                    """),
                    {"nome": nome, "nome_guerra": nome_guerra, "email": email, "matricula": matricula}
                )

        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("admin.index"))    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT matricula, nome, nome_guerra, email FROM usuario_sistema WHERE matricula = :matricula"),
            {"matricula": matricula}
        ).fetchone()

    if not result:
        flash("Usuário não encontrado!", "error")
        return redirect(url_for("admin.index"))

    usuario = dict(result._mapping)
    return render_template("admin/edit.html", usuario=usuario)

# ❌ Excluir usuário sistema
@admin_bp.route("/delete/<matricula>", methods=["POST"])
def delete_user(matricula):
    engine = get_db_connection()
    with engine.begin() as conn:        
        conn.execute(
            text("DELETE FROM usuario_perfis WHERE matricula = :matricula"),
            {"matricula": matricula}
        )        
        conn.execute(
            text("DELETE FROM usuario_sistema WHERE matricula = :matricula"),
            {"matricula": matricula}
        )
    flash("Usuário e seus vínculos de perfis foram removidos!", "info")
    return redirect(url_for("admin.index"))

@admin_bp.route("/alunos")
def gerenciar_alunos():
    return render_template("admin/alunos.html")

@admin_bp.route("/permissoes")
def gerenciar_permissoes():
    return render_template("admin/permissoes.html")

#usuário sistema
@admin_bp.route("/buscar", methods=["GET"])
def buscar_usuario():
    if session.get("perfil") != "ADMIN":
        flash("Acesso restrito", "error")
        return redirect(url_for("login_instrutor"))

    matricula = request.args.get("matricula")
    usuarios = []

    engine = get_db_connection()
    with engine.connect() as conn:  
        if matricula:
            query = text("""
                SELECT matricula, nome, nome_guerra, email 
                FROM usuario_sistema 
                WHERE matricula = :matricula
            """)
            result = conn.execute(query, {"matricula": matricula}).fetchall()
        else:
            query = text("""
                SELECT matricula, nome, nome_guerra, email 
                FROM usuario_sistema
                ORDER BY nome_guerra
            """)
            result = conn.execute(query).fetchall()

        usuarios = [dict(row._mapping) for row in result]

    return render_template("admin/index.html", usuarios=usuarios)
#permissão sistema
@admin_bp.route("/buscar_permissao")
def buscar_permissao():
    if session.get("perfil") != "ADMIN":
        flash("Acesso restrito", "error")
        return redirect(url_for("login_instrutor"))

    matricula = request.args.get("matricula")
    usuario = None

    if matricula:
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT matricula, nome FROM usuario_sistema WHERE matricula = :matricula"),
                {"matricula": matricula}
            ).fetchone()
            if result:
                usuario = dict(result._mapping)

    return render_template("admin/index.html", usuario=usuario)

#permissão sistema
@admin_bp.route("/permissoes/<matricula>", methods=["GET", "POST"])
def gerenciar_permissao_usuario(matricula):
    if session.get("perfil") != "ADMIN":
        flash("Acesso restrito", "error")
        return redirect(url_for("login_instrutor"))

    engine = get_db_connection()
    usuario, perfis, perfis_usuario = None, [], []

    with engine.connect() as conn:
        usuario = conn.execute(
            text("SELECT matricula, nome FROM usuario_sistema WHERE matricula = :matricula"),
            {"matricula": matricula}
        ).fetchone()

        perfis = conn.execute(text("SELECT id, nome FROM perfis")).fetchall()

        perfis_usuario = conn.execute(
            text("SELECT perfil_id FROM usuario_perfis WHERE matricula = :matricula"),
            {"matricula": matricula}
        ).fetchall()
        perfis_usuario = [row.perfil_id for row in perfis_usuario]

        if request.method == "POST":
            novos = request.form.getlist("perfis")            
            conn.execute(
                text("DELETE FROM usuario_perfis WHERE matricula = :matricula"),
                {"matricula": matricula}
            )
            
            for p in novos:
                conn.execute(
                    text("INSERT INTO usuario_perfis (matricula, perfil_id) VALUES (:matricula, :perfil_id)"),
                    {"matricula": matricula, "perfil_id": p}
                )
            conn.commit()

            flash("Permissões atualizadas com sucesso!", "success")
            return redirect(url_for("admin.index"))

    return render_template(
        "admin/permissoes_usuario.html",
        usuario=dict(usuario._mapping),
        perfis=[dict(p._mapping) for p in perfis],
        perfis_usuario=perfis_usuario
    )

@admin_bp.route("/alunos/consultar", methods=["GET"])
def consultar_alunos():
    engine = get_db_connection()
    re = request.args.get("re", "").strip()
    nome = request.args.get("nome", "").strip()
    pelotao = request.args.get("pelotao", "").strip()
    curso = request.args.get("curso", "").strip()
    page = int(request.args.get("page", 1))  # página atual (default=1)
    per_page = 20  # 🔥 registros por página
    offset = (page - 1) * per_page

    query = "SELECT re, nome, pelotao, curso FROM students WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM students WHERE 1=1"
    params = {}

    if re:
        query += " AND re = :re"
        count_query += " AND re = :re"
        params["re"] = re
    if nome:
        query += " AND nome LIKE :nome"
        count_query += " AND nome LIKE :nome"
        params["nome"] = f"%{nome}%"
    if pelotao:
        query += " AND pelotao = :pelotao"
        count_query += " AND pelotao = :pelotao"
        params["pelotao"] = pelotao
    if curso:
        query += " AND curso = :curso"
        count_query += " AND curso = :curso"
        params["curso"] = curso

    # 🔹 adiciona paginação
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = per_page
    params["offset"] = offset

    with engine.connect() as conn:
        result = conn.execute(text(query), params).fetchall()
        alunos = [dict(row._mapping) for row in result]

        total = conn.execute(text(count_query), params).scalar()  # total de registros
        total_pages = (total + per_page - 1) // per_page  # arredonda p/ cima

        pelotoes = [r[0] for r in conn.execute(text("SELECT DISTINCT pelotao FROM students")).fetchall()]
        cursos = [r[0] for r in conn.execute(text("SELECT DISTINCT curso FROM students")).fetchall()]

    return render_template(
        "admin/alunos/consultar.html",
        alunos=alunos,
        pelotoes=pelotoes,
        cursos=cursos,
        page=page,
        total_pages=total_pages
    )

#Gestão de Alunos atividade de ensino
# Editar aluno
@admin_bp.route("/alunos/edit/<string:re>", methods=["GET", "POST"])
def edit_aluno(re):
    engine = get_db_connection()

    # Buscar aluno pelo RE atual
    with engine.connect() as conn:
        aluno = conn.execute(
            text("SELECT re, nome, pelotao, curso FROM students WHERE re = :re"),
            {"re": re}
        ).fetchone()

    if not aluno:
        flash("Aluno não encontrado!", "error")
        return redirect(url_for("admin.consultar_alunos"))  

    if request.method == "POST":
        novo_re = request.form.get("re").strip()
        nome = request.form.get("nome").strip()
        pelotao = request.form.get("pelotao").strip()
        curso = request.form.get("curso").strip()

        if not novo_re or not nome or not pelotao or not curso:
            flash("Todos os campos são obrigatórios!", "error")
            return redirect(url_for("admin.edit_aluno", re=re))  

        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE students
                        SET re = :novo_re, nome = :nome, pelotao = :pelotao, curso = :curso
                        WHERE re = :re_antigo
                    """),
                    {
                        "novo_re": novo_re,
                        "nome": nome,
                        "pelotao": pelotao,
                        "curso": curso,
                        "re_antigo": re
                    }
                )

            flash("Aluno atualizado com sucesso!", "success")
            return redirect(url_for("admin.consultar_alunos"))  

        except Exception as e:
            flash(f"Erro ao atualizar aluno: {e}", "error")
            return redirect(url_for("admin.edit_aluno", re=re))  

    return render_template("admin/alunos/edit.html", aluno=aluno)

#Gestão de Alunos atividade de ensino
# Excluir aluno
@admin_bp.route("/alunos/delete/<string:re>", methods=["POST"])
def delete_aluno(re):
    try:
        engine = get_db_connection()
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM students WHERE re = :re"),
                {"re": re}
            )
        flash("Aluno excluído com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao excluir aluno: {e}", "error")

    return redirect(url_for("admin.consultar_alunos"))

#Gestão de Alunos atividade de ensino
# Criar aluno manualmente
@admin_bp.route("/alunos/create", methods=["GET", "POST"])
def create_aluno():
    if request.method == "POST":
        re = request.form.get("re").strip()
        nome = request.form.get("nome").strip()
        pelotao = request.form.get("pelotao").strip()
        curso = request.form.get("curso").strip()

        if not re or not nome or not pelotao or not curso:
            flash("Todos os campos são obrigatórios!", "error")
            return redirect(url_for("admin.create_aluno"))

        try:
            engine = get_db_connection()
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO students (re, nome, pelotao, curso)
                    VALUES (:re, :nome, :pelotao, :curso)
                    ON DUPLICATE KEY UPDATE
                        nome = VALUES(nome),
                        pelotao = VALUES(pelotao),
                        curso = VALUES(curso)
                """), {
                    "re": re,
                    "nome": nome,
                    "pelotao": pelotao,
                    "curso": curso
                })

            flash("Aluno salvo com sucesso!", "success")
            return redirect(url_for("admin.alunos.create"))

        except Exception as e:
            flash(f"Erro ao salvar aluno: {e}", "error")
            return redirect(url_for("admin.create_aluno"))

    return render_template("admin/alunos/create.html")  

#Gestão de Alunos atividade de ensino
@admin_bp.route("/alunos/import", methods=["GET", "POST"])
def import_alunos_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Nenhum arquivo selecionado!", "error")
            return redirect(url_for("admin.import_alunos_csv"))

        try:
            # Lê o conteúdo do arquivo
            content = file.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            file.stream.seek(0)  # 🔄 volta para o início do arquivo
            content = file.stream.read().decode("latin-1")

            # Detecta separador (vírgula ou ponto e vírgula)
            if ";" in content:
                df = pd.read_csv(StringIO(content), sep=";")
            else:
                df = pd.read_csv(StringIO(content), sep=",")

            # Normaliza nomes das colunas -> minúsculo
            df.columns = df.columns.str.strip().str.lower()

            # Verifica colunas obrigatórias
            required_cols = {"re", "nome", "pelotao", "curso"}
            if not required_cols.issubset(set(df.columns)):
                flash("O CSV deve conter as colunas: re, nome, pelotao, curso", "error")
                return redirect(url_for("admin.import_alunos_csv"))

            # Insere ou atualiza alunos
            engine = get_db_connection()
            with engine.begin() as conn:
                for _, row in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO students (re, nome, pelotao, curso)
                        VALUES (:re, :nome, :pelotao, :curso)
                        ON DUPLICATE KEY UPDATE
                            nome = VALUES(nome),
                            pelotao = VALUES(pelotao),
                            curso = VALUES(curso)
                    """), {
                        "re": str(row["re"]).strip(),
                        "nome": str(row["nome"]).strip(),
                        "pelotao": str(row["pelotao"]).strip(),
                        "curso": str(row["curso"]).strip(),
                    })

            flash("Alunos importados/atualizados com sucesso!", "success")
            return redirect(url_for("admin.index"))

        except Exception as e:
            flash(f"Erro ao importar CSV: {e}", "error")
            return redirect(url_for("admin.import_alunos_csv"))

    return render_template("admin/alunos/import_csv.html")

# 📌 Listar usuários online
@admin_bp.route("/usuarios_online")
def usuarios_online():
    engine = get_db_connection()
    with engine.connect() as conn:
        usuarios = conn.execute(text("""
            SELECT id, user_id, user_type, nome, inicio 
            FROM user_sessions 
            WHERE ativo = 1
            ORDER BY inicio DESC
        """)).fetchall()
    usuarios = [dict(row._mapping) for row in usuarios]

    total = len(usuarios)
    return render_template("admin/usuarios_online.html", usuarios=usuarios, total=total)

# 📌 Encerrar sessões em massa
@admin_bp.route("/usuarios_online/logout/<string:tipo>", methods=["POST"])
def logout_usuarios_online(tipo):
    engine = get_db_connection()
    with engine.begin() as conn:
        if tipo == "todos":
            conn.execute(text("UPDATE user_sessions SET fim = NOW(), ativo = 0 WHERE ativo = 1"))
        elif tipo == "alunos":
            conn.execute(text("UPDATE user_sessions SET fim = NOW(), ativo = 0 WHERE ativo = 1 AND user_type = 'aluno'"))
        elif tipo == "sistema":
            conn.execute(text("UPDATE user_sessions SET fim = NOW(), ativo = 0 WHERE ativo = 1 AND user_type = 'sistema'"))
    flash(f"Sessões de {tipo} encerradas.", "info")
    return redirect(url_for("admin.usuarios_online"))

# 📌 Encerrar sessão individual
@admin_bp.route("/usuarios_online/logout_one/<int:session_id>", methods=["POST"])
def logout_usuario_individual(session_id):
    engine = get_db_connection()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE user_sessions SET fim = NOW(), ativo = 0 WHERE id = :id"),
            {"id": session_id}
        )
    flash("Usuário deslogado com sucesso.", "success")
    return redirect(url_for("admin.usuarios_online"))

# 📌 Página de Auditoria
@admin_bp.route("/auditoria", methods=["GET"])
def auditoria():
    user_id = request.args.get("user_id", "").strip()
    nome = request.args.get("nome", "").strip()
    data_inicio = request.args.get("data_inicio", "").strip()
    data_fim = request.args.get("data_fim", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 20  # 🔹 registros por página

    query = """
        SELECT id, session_id, user_type, user_id, nome, acao, detalhes, data_hora, ip_address
        FROM user_audit_log
        WHERE 1=1
    """

    params = {}

    if user_id:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id
    if nome:
        query += " AND nome LIKE :nome"
        params["nome"] = f"%{nome}%"
    if data_inicio:
        query += " AND DATE(data_hora) >= :data_inicio"
        params["data_inicio"] = data_inicio
    if data_fim:
        query += " AND DATE(data_hora) <= :data_fim"
        params["data_fim"] = data_fim

    # 🔹 Conta total de registros para paginação
    count_query = f"SELECT COUNT(*) FROM ({query}) as total"
    engine = get_db_connection()
    with engine.connect() as conn:
        total = conn.execute(text(count_query), params).scalar()

        # 🔹 Aplica paginação
        query += " ORDER BY data_hora DESC LIMIT :limit OFFSET :offset"
        params["limit"] = per_page
        params["offset"] = (page - 1) * per_page

        result = conn.execute(text(query), params).fetchall()
        registros = [dict(r._mapping) for r in result]

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "admin/auditoria.html",
        logs=registros,
        page=page,
        total_pages=total_pages
    )

app.register_blueprint(admin_bp)

#Controle de acesso e auditoria
def registrar_sessao(user_type, user_id, nome, ip, user_agent):
    """Cria sessão no banco ao logar"""
    engine = get_db_connection()
    token = secrets.token_hex(32)
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO user_sessions (user_type, user_id, nome, session_token, inicio, ativo, ip_address, user_agent)
            VALUES (:user_type, :user_id, :nome, :token, NOW(), 1, :ip, :ua)
        """), {
            "user_type": user_type,
            "user_id": user_id,
            "nome": nome,
            "token": token,
            "ip": ip,
            "ua": user_agent
        })
        session_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    session["session_token"] = token
    session["session_id"] = session_id
    return token

def encerrar_sessao():
    """Finaliza sessão no banco ao sair"""
    token = session.get("session_token")
    if token:
        engine = get_db_connection()
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE user_sessions 
                SET fim = NOW(), ativo = 0
                WHERE session_token = :token
            """), {"token": token})
    session.clear()

def registrar_auditoria(acao, detalhes=None, user_id=None, nome=None, user_type=None):
    """Registra ação feita pelo usuário logado"""
    session_id = session.get("session_id")
    if not session_id:
        return

    # Se não foi passado, tenta buscar da sessão
    if not user_id:
        if "re" in session:  
            user_id = session["re"]
            user_type = "student"
            nome = session.get("nome")
        elif "usuario" in session:  
            user_id = session.get("user_id") or session["usuario"]
            user_type = "sistema"
            nome = session.get("usuario")
        else:
            user_id = None
            user_type = "desconhecido"

    engine = get_db_connection()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO user_audit_log 
                (session_id, user_id, nome, user_type, acao, detalhes, data_hora, ip_address)
                VALUES (:sid, :uid, :nome, :utype, :acao, :detalhes, NOW(), :ip)
            """),
            {
                "sid": session_id,
                "uid": user_id,
                "nome": nome,
                "utype": user_type,
                "acao": acao,
                "detalhes": detalhes,
                "ip": request.remote_addr
            }
        )

#Controle de Materiais
#Controle e-mail
@app.route("/materiais/emails")
def materiais_emails():
    if session.get("perfil") != "SUPORTE":
        return redirect(url_for("login_instrutor"))

    registrar_auditoria(
        acao="Acesso",
        detalhes="Usuário acessou Gestão de E-mails",
        user_id=session.get('user_id'),
        nome=session.get('usuario'),
        user_type="sistema"
    )

    unidade_id = request.args.get("unidade_id")
    tipo_id = request.args.get("tipo_id")
    email = request.args.get("email")
    responsavel = request.args.get("responsavel")
    cpf = request.args.get("cpf")

    query = """
        SELECT e.id, u.nome as unidade, t.nome as tipo, e.email,
               e.responsavel, e.cpf, e.numero_processo, e.data_cadastro, e.observacao
        FROM emails e
        JOIN unidades u ON e.unidade_id = u.id
        JOIN tipos t ON e.tipo_id = t.id
        WHERE 1=1
    """
    params = {}

    if unidade_id:
        query += " AND e.unidade_id = :unidade_id"
        params["unidade_id"] = unidade_id
    if tipo_id:
        query += " AND e.tipo_id = :tipo_id"
        params["tipo_id"] = tipo_id
    if email:
        query += " AND e.email LIKE :email"
        params["email"] = f"%{email}%"
    if responsavel:
        query += " AND e.responsavel LIKE :responsavel"
        params["responsavel"] = f"%{responsavel}%"
    if cpf:
        query += " AND e.cpf LIKE :cpf"
        params["cpf"] = f"%{cpf}%"

    query += " ORDER BY e.data_cadastro DESC"

    engine = get_db_connection()
    with engine.connect() as conn:
        emails = conn.execute(text(query), params).fetchall()
        unidades = conn.execute(text("SELECT id, nome FROM unidades")).fetchall()
        tipos = conn.execute(text("SELECT id, nome FROM tipos")).fetchall()

    return render_template("materiais/emails/index.html", emails=emails, unidades=unidades, tipos=tipos)

# ➕ Criar E-mail
@app.route("/materiais/emails/create", methods=["GET", "POST"])
def materiais_emails_create():
    if session.get("perfil") != "SUPORTE":
        return redirect(url_for("login_instrutor"))

    if request.method == "POST":
        unidade_id = request.form["unidade_id"]
        tipo_id = request.form["tipo_id"]
        email = request.form["email"].strip()
        responsavel = request.form.get("responsavel")
        cpf = request.form.get("cpf")
        numero_processo = request.form.get("numero_processo")
        observacao = request.form.get("observacao")

        engine = get_db_connection()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO emails (unidade_id, tipo_id, email, responsavel, cpf, numero_processo, observacao, data_cadastro)
                VALUES (:unidade_id, :tipo_id, :email, :responsavel, :cpf, :numero_processo, :observacao, NOW())
            """), {
                "unidade_id": unidade_id,
                "tipo_id": tipo_id,
                "email": email,
                "responsavel": responsavel,
                "cpf": cpf,
                "numero_processo": numero_processo,
                "observacao": observacao
            })

        registrar_auditoria(
            acao="Create",
            detalhes=f"E-mail {email} cadastrado",
            user_id=session.get("user_id"),
            nome=session.get("usuario"),
            user_type="sistema"
        )

        flash("E-mail cadastrado com sucesso!", "success")
        return redirect(url_for("materiais_emails"))

    engine = get_db_connection()
    with engine.connect() as conn:
        unidades = conn.execute(text("SELECT id, nome FROM unidades ORDER BY nome")).fetchall()
        tipos = conn.execute(text("SELECT id, nome FROM tipos ORDER BY nome")).fetchall()

    return render_template("materiais/emails/create.html", unidades=unidades, tipos=tipos)

# ✏️ Editar E-mail
@app.route("/materiais/emails/edit/<int:id>", methods=["GET", "POST"])
def materiais_emails_edit(id):
    if session.get("perfil") != "SUPORTE":
        return redirect(url_for("login_instrutor"))

    engine = get_db_connection()
    with engine.connect() as conn:
        email_data = conn.execute(text("SELECT * FROM emails WHERE id=:id"), {"id": id}).fetchone()

    if not email_data:
        flash("Registro não encontrado!", "error")
        return redirect(url_for("materiais_emails"))

    if request.method == "POST":
        unidade_id = request.form["unidade_id"]
        tipo_id = request.form["tipo_id"]
        email = request.form["email"].strip()
        responsavel = request.form.get("responsavel")
        cpf = request.form.get("cpf")
        numero_processo = request.form.get("numero_processo")
        observacao = request.form.get("observacao")

        engine = get_db_connection()
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE emails
                SET unidade_id=:unidade_id, tipo_id=:tipo_id, email=:email,
                    responsavel=:responsavel, cpf=:cpf, numero_processo=:numero_processo,
                    observacao=:observacao
                WHERE id=:id
            """), {
                "unidade_id": unidade_id,
                "tipo_id": tipo_id,
                "email": email,
                "responsavel": responsavel,
                "cpf": cpf,
                "numero_processo": numero_processo,
                "observacao": observacao,
                "id": id
            })

        registrar_auditoria(
            acao="Update",
            detalhes=f"E-mail {email} atualizado (ID {id})",
            user_id=session.get("user_id"),
            nome=session.get("usuario"),
            user_type="sistema"
        )

        flash("Registro atualizado!", "success")
        return redirect(url_for("materiais_emails"))

    engine = get_db_connection()
    with engine.connect() as conn:
        unidades = conn.execute(text("SELECT id, nome FROM unidades ORDER BY nome")).fetchall()
        tipos = conn.execute(text("SELECT id, nome FROM tipos ORDER BY nome")).fetchall()

    return render_template("materiais/emails/edit.html", email=email_data, unidades=unidades, tipos=tipos)

# ❌ Excluir E-mail
@app.route("/materiais/emails/delete/<int:id>", methods=["POST"])
def materiais_emails_delete(id):
    if session.get("perfil") != "SUPORTE":
        return redirect(url_for("login_instrutor"))

    engine = get_db_connection()
    with engine.begin() as conn:
        email_data = conn.execute(text("SELECT email FROM emails WHERE id=:id"), {"id": id}).fetchone()
        conn.execute(text("DELETE FROM emails WHERE id=:id"), {"id": id})

    registrar_auditoria(
        acao="Delete",
        detalhes=f"E-mail {email_data.email if email_data else id} excluído",
        user_id=session.get("user_id"),
        nome=session.get("usuario"),
        user_type="sistema"
    )

    flash("E-mail removido com sucesso!", "info")
    return redirect(url_for("materiais_emails"))

# 📦 Listagem de Chips
@app.route("/materiais/chips")
def materiais_chips():
    if session.get("perfil") != "SUPORTE":
        return redirect(url_for("login_instrutor"))

    registrar_auditoria(
        acao="Acesso",
        detalhes="Usuário acessou Gestão de Chips Telefônicos",
        user_id=session.get('user_id'),
        nome=session.get('usuario'),
        user_type="sistema"
    )

    unidade_id = request.args.get("unidade_id")
    numero_chip = request.args.get("numero_chip")
    numero_processo = request.args.get("numero_processo")

    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    query = """
        SELECT c.id, u.nome as unidade, c.numero_chip, c.numero_processo,
               c.data_cadastro, c.observacao
        FROM chips c
        JOIN unidades u ON c.unidade_id = u.id
        WHERE 1=1
    """
    params = {}

    if unidade_id:
        query += " AND c.unidade_id = :unidade_id"
        params["unidade_id"] = unidade_id
    if numero_chip:
        query += " AND c.numero_chip LIKE :numero_chip"
        params["numero_chip"] = f"%{numero_chip}%"
    if numero_processo:
        query += " AND c.numero_processo LIKE :numero_processo"
        params["numero_processo"] = f"%{numero_processo}%"

    count_query = f"SELECT COUNT(*) FROM ({query}) as total"
    query += " ORDER BY c.data_cadastro DESC LIMIT :limit OFFSET :offset"

    engine = get_db_connection()
    with engine.connect() as conn:
        total = conn.execute(text(count_query), params).scalar()
        chips = conn.execute(text(query), {**params, "limit": per_page, "offset": offset}).fetchall()
        unidades = conn.execute(text("SELECT id, nome FROM unidades")).fetchall()

    total_pages = (total + per_page - 1) // per_page

    return render_template("materiais/chips/index.html",
                           chips=chips,
                           unidades=unidades,
                           page=page,
                           total_pages=total_pages)

# ➕ Create
@app.route("/materiais/chips/create", methods=["GET", "POST"])
def materiais_chips_create():
    if request.method == "POST":
        unidade_id = request.form.get("unidade_id")
        numero_chip = request.form.get("numero_chip")
        numero_processo = request.form.get("numero_processo")
        observacao = request.form.get("observacao")

        engine = get_db_connection()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO chips (unidade_id, numero_chip, numero_processo, observacao)
                VALUES (:unidade_id, :numero_chip, :numero_processo, :observacao)
            """), {
                "unidade_id": unidade_id,
                "numero_chip": numero_chip,
                "numero_processo": numero_processo,
                "observacao": observacao
            })

        registrar_auditoria("Create", f"Cadastro de chip {numero_chip}")
        flash("Chip cadastrado com sucesso!", "success")
        return redirect(url_for("materiais_chips"))

    engine = get_db_connection()
    with engine.connect() as conn:
        unidades = conn.execute(text("SELECT id, nome FROM unidades")).fetchall()

    return render_template("materiais/chips/create.html", unidades=unidades)

# ✏️ Edit
@app.route("/materiais/chips/edit/<int:id>", methods=["GET", "POST"])
def materiais_chips_edit(id):
    engine = get_db_connection()
    if request.method == "POST":
        unidade_id = request.form.get("unidade_id")
        numero_chip = request.form.get("numero_chip")
        numero_processo = request.form.get("numero_processo")
        observacao = request.form.get("observacao")

        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE chips
                SET unidade_id=:unidade_id, numero_chip=:numero_chip,
                    numero_processo=:numero_processo, observacao=:observacao
                WHERE id=:id
            """), {
                "id": id,
                "unidade_id": unidade_id,
                "numero_chip": numero_chip,
                "numero_processo": numero_processo,
                "observacao": observacao
            })

        registrar_auditoria("Edit", f"Edição de chip ID {id}")
        flash("Chip atualizado com sucesso!", "success")
        return redirect(url_for("materiais_chips"))

    with engine.connect() as conn:
        chip = conn.execute(text("SELECT * FROM chips WHERE id=:id"), {"id": id}).fetchone()
        unidades = conn.execute(text("SELECT id, nome FROM unidades")).fetchall()

    return render_template("materiais/chips/edit.html", chip=chip, unidades=unidades)

# ❌ Delete
@app.route("/materiais/chips/delete/<int:id>", methods=["POST"])
def materiais_chips_delete(id):
    engine = get_db_connection()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM chips WHERE id=:id"), {"id": id})

    registrar_auditoria("Delete", f"Exclusão de chip ID {id}")
    flash("Chip excluído com sucesso!", "info")
    return redirect(url_for("materiais_chips"))


@app.route("/siseg/cadastro-efetivo", methods=["GET", "POST"])
def siseg_cadastro_efetivo():
    if request.method == "POST":
        status_msgs = []

        matriculas_raw = request.form.get("matriculas", "").strip()
        if not matriculas_raw:
            flash("Matrícula é obrigatória.", "error")
            return redirect(url_for("siseg_cadastro_efetivo"))

        matriculas = [m.strip() for m in matriculas_raw.split(";") if m.strip()]
        total_inseridos, total_atualizados, total_nao_encontrados = 0, 0, 0

        # conexões com os bancos
        with engine_main.begin() as conn_main, engine_extern.connect() as conn_ext:
            for mat in matriculas:
                militar = conn_ext.execute(
                    text("SELECT * FROM vw_aplicacao_suporte WHERE matricula = :mat"),
                    {"mat": mat}
                ).mappings().fetchone()

                if militar:
                    existe = conn_main.execute(
                        text("SELECT 1 FROM dados_importados_militar WHERE matricula = :mat"),
                        {"mat": militar["matricula"]}
                    ).fetchone()

                    if existe:
                        conn_main.execute(text("""
                            UPDATE dados_importados_militar
                            SET nome_militar = :nome_completo,
                                nome_guerra  = :nome_guerra,
                                cpf          = :cpf,
                                telefone     = :telefone,
                                graduacao    = :graduacao,
                                email        = :email,
                                unidade_nome = :unidade_nome
                            WHERE matricula = :matricula
                        """), {
                            "matricula": militar["matricula"],
                            "nome_completo": militar["nome"],
                            "nome_guerra": militar["nome_guerra"],
                            "cpf": militar["cpf"],
                            "telefone": militar["telefone_celular_1"],
                            "graduacao": militar["posto_graduacao"],
                            "email": militar["email"],
                            "unidade_nome": militar["id_unidade_movimentacao"]
                        })
                        registrar_auditoria("Update", f"Cadastro Efetivo atualizado - Matrícula {militar['matricula']}")
                        total_atualizados += 1
                    else:
                        conn_main.execute(text("""
                            INSERT INTO dados_importados_militar
                            (tipo, matricula, nome_militar, nome_guerra, cpf, telefone, graduacao, email,
                             unidade_nome, data_cadastro)
                            VALUES ('efetivo', :matricula, :nome_completo, :nome_guerra, :cpf, :telefone,
                                    :graduacao, :email, :unidade_nome, NOW())
                        """), {
                            "matricula": militar["matricula"],
                            "nome_completo": militar["nome"],
                            "nome_guerra": militar["nome_guerra"],
                            "cpf": militar["cpf"],
                            "telefone": militar["telefone_celular_1"],
                            "graduacao": militar["posto_graduacao"],
                            "email": militar["email"],
                            "unidade_nome": militar["id_unidade_movimentacao"]
                        })
                        registrar_auditoria("Create", f"Cadastro Efetivo inserido - Matrícula {militar['matricula']}")
                        total_inseridos += 1
                else:
                    registrar_auditoria("Erro", f"Matrícula não encontrada no SIGA: {mat}")
                    total_nao_encontrados += 1

        if total_inseridos == 0 and total_atualizados == 0:
            status_msgs.append(f"❌ Nenhuma matrícula encontrada ({total_nao_encontrados} não encontrado(s)). Processo finalizado.")
            return render_template("siseg/status.html", status_msgs=status_msgs)

        status_msgs.append(
            f"✅ Dados coletados: {total_inseridos} inserido(s), "
            f"{total_atualizados} atualizado(s), "
            f"{total_nao_encontrados} não encontrado(s)."
        )

        # ---------- Iniciando login no SISEG ----------
        status_msgs.append("🔄 Iniciando login no SISEG...")

        try:
            login_driver = login_siseg(headless=False)

            if login_driver:
                session["siseg_token"] = "ok"
                status_msgs.append("✅ Login no SISEG realizado com sucesso.")

                status_msgs = atualizar_efetivo(engine_main, status_msgs, matriculas, login_driver)

                login_driver.quit()
            else:
                status_msgs.append("❌ Falha no login do SISEG.")            

        except Exception as e:
            status_msgs.append(f"❌ Erro ao conectar no SISEG: {e}")

        return render_template("siseg/status.html", status_msgs=status_msgs)

    # GET → tela inicial
    return render_template("siseg/cadastro_efetivo.html")


   


## parei aqui

# Página principal do SISEG (CZEG-sysait)
@app.route("/siseg", endpoint="siseg_index")
def siseg_home():
    registrar_auditoria("Acesso", "Usuário acessou Tecnologia Mobile SISEG - SYS AIT")
    return render_template("siseg/index.html")


# Atendimento GLPI (placeholder por enquanto)
@app.route("/glpi")
def glpi_home():
    registrar_auditoria("Acesso", "Usuário acessou Atendimento GLPI")
    return "Página de Atendimento GLPI (em construção)"


@app.route("/siseg/cadastro-usuario")
def siseg_cadastro_usuario():    
    if request.method == "POST":
        matriculas_raw = request.form.get("matriculas", "").strip()
        perfil_id = request.form.get("perfil_id")
        numero_glpi = request.form.get("numero_glpi") or None

        if not matriculas_raw or not perfil_id:
            flash("Matrícula e perfil são obrigatórios.", "error")
            return redirect(url_for("siseg_cadastro_efetivo"))

        matriculas = [m.strip() for m in matriculas_raw.split(";") if m.strip()]
        total_inseridos, total_nao_encontrados = 0, 0

        with engine_main.begin() as conn_main, engine_extern.connect() as conn_ext:
            for mat in matriculas:
                militar = conn_ext.execute(
                    text("SELECT * FROM vw_militares_detalhes WHERE matricula = :mat"),
                    {"mat": mat}
                ).fetchone()

                if militar:
                    # Buscar unidade_id no banco local
                    row = conn_main.execute(
                        text("SELECT id, nome FROM unidades WHERE nome = :nome"),
                        {"nome": militar.unidade_lotacao}
                    ).fetchone()

                    unidade_id = row.id if row else None
                    unidade_nome = militar.unidade_lotacao

                    # Inserir no cadastro principal
                    conn_main.execute(text("""
                        INSERT INTO cadastro_siseg 
                        (tipo, matricula, nome_militar, nome_guerra, cpf, telefone, graduacao, email,
                         unidade_id, unidade_nome, perfil_id, numero_glpi, data_cadastro)
                        VALUES ('efetivo', :matricula, :nome_completo, :nome_guerra, :cpf, :telefone, :graduacao,
                                :email, :unidade_id, :unidade_nome, :perfil_id, :numero_glpi, NOW())
                    """), {
                        "matricula": militar.matricula,
                        "nome_completo": militar.nome_completo,
                        "nome_guerra": militar.nome_guerra,
                        "cpf": militar.cpf,
                        "telefone": militar.telefone,
                        "graduacao": militar.graduacao,
                        "email": militar.email,
                        "unidade_id": unidade_id,
                        "unidade_nome": unidade_nome,
                        "perfil_id": perfil_id,
                        "numero_glpi": numero_glpi
                    })

                    registrar_auditoria("Create", f"Cadastro Efetivo - Matrícula {militar.matricula}")
                    total_inseridos += 1
                else:
                    registrar_auditoria("Erro", f"Matrícula não encontrada no SIGA: {mat}")
                    total_nao_encontrados += 1

        flash(f"{total_inseridos} cadastro(s) realizado(s), {total_nao_encontrados} matrícula(s) não encontradas.", "info")
        return redirect(url_for("siseg_cadastro_efetivo"))

    # GET → carregar selects
    with engine_main.connect() as conn:
        perfis = conn.execute(text("SELECT id, nome FROM perfil_acesso")).fetchall()
        unidades = conn.execute(text("SELECT id, nome FROM unidades")).fetchall()

    return render_template("siseg/cadastro_usuario.html", perfis=perfis, unidades=unidades)





@app.route("/siseg/atualizacao-efetivo")
def siseg_atualizacao_efetivo():
    return "Tela de Atualização de Efetivo siseg"



@app.route("/siseg/atualizacao-usuario")
def siseg_atualizacao_usuario():
    return "Tela de Atualização de Usuário siseg"

# Rotas CZT
@app.route("/sysait/cadastro-efetivo")
def sysait_cadastro_efetivo():
    return "Tela de Cadastro de Efetivo sysait"

@app.route("/sysait/atualizacao-efetivo")
def sysait_atualizacao_efetivo():
    return "Tela de Atualização de Efetivo sysait"

@app.route("/sysait/cadastro-usuario")
def sysait_cadastro_usuario():
    return "Tela de Cadastro de Usuário sysait"

@app.route("/sysait/atualizacao-usuario")
def sysait_atualizacao_usuario():
    return "Tela de Atualização de Usuário sysait"


# Rotas SISEG TREINAMENTO
@app.route("/siseg/treinamento/cadastro-efetivo")
def siseg_treinamento_cadastro_efetivo():
    registrar_auditoria("Acesso", "Usuário acessou Cadastro de Efetivo - SISEG Treinamento")
    return "Tela de Cadastro de Efetivo - SISEG Treinamento"

@app.route("/siseg/treinamento/atualizacao-efetivo")
def siseg_treinamento_atualizacao_efetivo():
    registrar_auditoria("Acesso", "Usuário acessou Atualização de Efetivo - SISEG Treinamento")
    return "Tela de Atualização de Efetivo - SISEG Treinamento"

@app.route("/siseg/treinamento/cadastro-usuario")
def siseg_treinamento_cadastro_usuario():
    registrar_auditoria("Acesso", "Usuário acessou Cadastro de Usuário - SISEG Treinamento")
    return "Tela de Cadastro de Usuário - SISEG Treinamento"

@app.route("/siseg/treinamento/atualizacao-usuario")
def siseg_treinamento_atualizacao_usuario():
    registrar_auditoria("Acesso", "Usuário acessou Atualização de Usuário - SISEG Treinamento")
    return "Tela de Atualização de Usuário - SISEG Treinamento"



@app.route("/siseg/cadastro", methods=["GET", "POST"])
def siseg_cadastro():
    engine = get_db_connection()

    if request.method == "POST":
        matriculas = request.form.getlist("matriculas[]")
        tipo = request.form.get("tipo")

        nome_militar = request.form.get("nome_militar")
        nome_usuario = request.form.get("nome_usuario")
        perfil_usuario = request.form.get("perfil_usuario")
        numero_glpi = request.form.get("numero_glpi")

        perfil_global = request.form.get("perfil_global")
        unidade_global = request.form.get("unidade_global")

        perfis_individuais = request.form.getlist("perfis[]")
        unidades_individuais = request.form.getlist("unidades[]")

        with engine.begin() as conn:
            for i, matricula in enumerate(matriculas):
                perfil_id = perfil_global or perfis_individuais[i]
                unidade_id = unidade_global or unidades_individuais[i]

                conn.execute(text("""
                    INSERT INTO cadastro_siseg 
                    (tipo, matricula, nome_militar, nome_usuario, perfil_usuario, numero_glpi, perfil_id, unidade_id)
                    VALUES (:tipo, :matricula, :nome_militar, :nome_usuario, :perfil_usuario, :numero_glpi, :perfil_id, :unidade_id)
                """), {
                    "tipo": tipo,
                    "matricula": matricula,
                    "nome_militar": nome_militar,
                    "nome_usuario": nome_usuario,
                    "perfil_usuario": perfil_usuario,
                    "numero_glpi": numero_glpi,
                    "perfil_id": perfil_id,
                    "unidade_id": unidade_id
                })

        registrar_auditoria("Create", f"Cadastro {tipo} SISEG - {len(matriculas)} registro(s)")
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("siseg_cadastro"))

    with engine.connect() as conn:
        perfis = conn.execute(text("SELECT id, nome FROM perfis_acesso")).fetchall()
        unidades = conn.execute(text("SELECT id, nome FROM unidades")).fetchall()

    return render_template("siseg/cadastro.html", perfis=perfis, unidades=unidades)


# uso normal

# if __name__ == '__main__':
#     app.run(debug=True)

#USO docker
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
