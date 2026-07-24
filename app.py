from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "vortasky_secret_key_produtividade"

NOME_BANCO = "smartpay_produtividade.db"

def inicializar_banco_dados():
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos_remessas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_pagamento DATE NOT NULL,
            nome_remessa TEXT NOT NULL,
            qtd_fornecedores INTEGER NOT NULL DEFAULT 0,
            qtd_processos INTEGER NOT NULL DEFAULT 0,
            qtd_contratos INTEGER NOT NULL DEFAULT 0,
            certidoes_renovadas INTEGER NOT NULL DEFAULT 0,
            pagamentos_parciais INTEGER NOT NULL DEFAULT 0,
            glosas_lancadas INTEGER NOT NULL DEFAULT 0,
            apostilamentos_bancarios INTEGER NOT NULL DEFAULT 0,
            pontuacao_total INTEGER NOT NULL,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            matricula_usuario TEXT
        )
    ''')
    
    try: cursor.execute("ALTER TABLE lancamentos_remessas ADD COLUMN matricula_usuario TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE lancamentos_remessas ADD COLUMN glosas_lancadas INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE lancamentos_remessas ADD COLUMN apostilamentos_bancarios INTEGER DEFAULT 0")
    except: pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_registro DATE NOT NULL,
            motivo TEXT NOT NULL,
            referencia TEXT,
            tempo_impacto REAL,
            observacoes TEXT,
            matricula_usuario TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            cargo TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM colaboradores WHERE matricula = "12345"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin)
            VALUES ('12345', 'Cássio Abreu', 'Gestor Financeiro', '30/12/95', 1)
        ''')
        
    conexao.commit()
    conexao.close()

inicializar_banco_dados()

def calcular_esforco(processos, contratos, certidoes, parciais, glosas, apostilamentos):
    return (processos * 1) + (contratos * 2) + (certidoes * 1) + (parciais * 1) + (glosas * 1) + (apostilamentos * 2)

@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dados = request.json if request.is_json else request.form
        usuario = dados.get('usuario')
        senha = dados.get('senha')

        conexao = sqlite3.connect(NOME_BANCO)
        cursor = conexao.cursor()
        cursor.execute('SELECT nome, cargo, is_admin FROM colaboradores WHERE matricula = ? AND data_nascimento = ?', (usuario, senha))
        user = cursor.fetchone()
        conexao.close()

        if user:
            session['usuario'] = usuario
            session['nome'] = user[0]
            session['cargo'] = user[1]
            session['is_admin'] = user[2]
            if request.is_json: return jsonify({"status": "sucesso", "redirect": url_for('index')}), 200
            return redirect(url_for('index'))
        else:
            msg_erro = "Matrícula ou data de nascimento incorretos."
            if request.is_json: return jsonify({"status": "erro", "mensagem": msg_erro}), 401
            return render_template('login.html', erro=msg_erro)
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# ROTAS: RELATÓRIOS DO ADMINISTRADOR (NOVO)
# ==========================================
@app.route('/api/admin/relatorios/remessas', methods=['GET'])
def admin_relatorio_remessas():
    if 'usuario' not in session or not session.get('is_admin'): return jsonify({"status": "erro", "mensagem": "Acesso negado"}), 403
    
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')
    matricula = request.args.get('matricula')
    
    query = '''
        SELECT r.*, c.nome as nome_colaborador
        FROM lancamentos_remessas r
        LEFT JOIN colaboradores c ON r.matricula_usuario = c.matricula
        WHERE 1=1
    '''
    params = []
    if inicio and fim:
        query += ' AND r.data_pagamento BETWEEN ? AND ?'
        params.extend([inicio, fim])
    if matricula and matricula != 'todos':
        query += ' AND r.matricula_usuario = ?'
        params.append(matricula)
        
    query += ' ORDER BY r.data_pagamento DESC, r.id DESC'

    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute(query, params)
    linhas = cursor.fetchall()
    
    total_pontos = sum(r['pontuacao_total'] for r in linhas)
    total_processos = sum(r['qtd_processos'] for r in linhas)
    
    resultado = {
        "metricas": {"pontos_totais": total_pontos, "processos_totais": total_processos, "total_remessas": len(linhas)},
        "dados": [dict(r) for r in linhas]
    }
    conexao.close()
    return jsonify(resultado), 200

@app.route('/api/admin/relatorios/ocorrencias', methods=['GET'])
def admin_relatorio_ocorrencias():
    if 'usuario' not in session or not session.get('is_admin'): return jsonify({"status": "erro"}), 403
    
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')
    matricula = request.args.get('matricula')

    query = '''
        SELECT o.*, c.nome as nome_colaborador
        FROM ocorrencias o
        LEFT JOIN colaboradores c ON o.matricula_usuario = c.matricula
        WHERE 1=1
    '''
    params = []
    if inicio and fim:
        query += ' AND o.data_registro BETWEEN ? AND ?'
        params.extend([inicio, fim])
    if matricula and matricula != 'todos':
        query += ' AND o.matricula_usuario = ?'
        params.append(matricula)
        
    query += ' ORDER BY o.data_registro DESC, o.id DESC'

    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute(query, params)
    linhas = cursor.fetchall()
    
    total_horas = sum(r['tempo_impacto'] for r in linhas if r['tempo_impacto'])
    
    resultado = {
        "metricas": {"total_ocorrencias": len(linhas), "total_horas": total_horas},
        "dados": [dict(r) for r in linhas]
    }
    conexao.close()
    return jsonify(resultado), 200


# ==========================================
# DEMAIS ROTAS EXISTENTES
# ==========================================
@app.route('/api/colaboradores', methods=['GET', 'POST'])
def api_colaboradores():
    if 'usuario' not in session or not session.get('is_admin'): return jsonify({"status": "erro"}), 403
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    if request.method == 'GET':
        cursor.execute('SELECT id, matricula, nome, cargo, data_nascimento, is_admin FROM colaboradores ORDER BY nome')
        colabs = [dict(row) for row in cursor.fetchall()]
        conexao.close()
        return jsonify(colabs), 200
    elif request.method == 'POST':
        dados = request.json
        try:
            is_admin = 1 if str(dados.get('is_admin')).lower() == 'true' or dados.get('is_admin') == True or dados.get('is_admin') == 1 else 0
            cursor.execute('INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin) VALUES (?, ?, ?, ?, ?)', 
                           (dados['matricula'], dados['nome'], dados['cargo'], dados['data_nascimento'], is_admin))
            conexao.commit()
            conexao.close()
            return jsonify({"status": "sucesso"}), 201
        except sqlite3.IntegrityError:
            conexao.close()
            return jsonify({"status": "erro", "mensagem": "Matrícula já cadastrada."}), 400

@app.route('/api/colaboradores/<int:id_colab>', methods=['PUT', 'DELETE'])
def gerir_colaborador(id_colab):
    if 'usuario' not in session or not session.get('is_admin'): return jsonify({"status": "erro"}), 403
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    if request.method == 'PUT':
        dados = request.json
        try:
            is_admin = 1 if str(dados.get('is_admin')).lower() == 'true' or dados.get('is_admin') == True or dados.get('is_admin') == 1 else 0
            cursor.execute('UPDATE colaboradores SET matricula = ?, nome = ?, cargo = ?, data_nascimento = ?, is_admin = ? WHERE id = ?', (dados['matricula'], dados['nome'], dados['cargo'], dados['data_nascimento'], is_admin, id_colab))
            conexao.commit()
            conexao.close()
            return jsonify({"status": "sucesso"}), 200
        except sqlite3.IntegrityError:
            conexao.close()
            return jsonify({"status": "erro", "mensagem": "Esta matrícula já está em uso."}), 400
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM colaboradores WHERE id = ?', (id_colab,))
        conexao.commit()
        conexao.close()
        return jsonify({"status": "sucesso"}), 200

@app.route('/api/metricas-dashboard', methods=['GET'])
def metricas_dashboard():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    matricula = session['usuario']
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    try:
        conexao = sqlite3.connect(NOME_BANCO)
        cursor = conexao.cursor()
        if data_inicio and data_fim:
            cursor.execute('SELECT TOTAL(pontuacao_total), TOTAL(qtd_processos), COUNT(id) FROM lancamentos_remessas WHERE matricula_usuario = ? AND data_pagamento BETWEEN ? AND ?', (matricula, data_inicio, data_fim))
        else:
            cursor.execute('SELECT TOTAL(pontuacao_total), TOTAL(qtd_processos), COUNT(id) FROM lancamentos_remessas WHERE matricula_usuario = ?', (matricula,))
        resultado = cursor.fetchone()
        conexao.close()
        return jsonify({"pontos_totais": int(resultado[0]) if resultado[0] else 0, "processos_totais": int(resultado[1]) if resultado[1] else 0, "total_remessas": int(resultado[2]) if resultado[2] else 0}), 200
    except Exception as e: return jsonify({"status": "erro"}), 500

@app.route('/api/salvar-lote', methods=['POST'])
def salvar_lote_remessa():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    dados = request.json
    matricula = session['usuario']
    pontuacao = calcular_esforco(int(dados.get('qtd_processos', 0)), int(dados.get('qtd_contratos', 0)), int(dados.get('certidoes_renovadas', 0)), int(dados.get('pagamentos_parciais', 0)), int(dados.get('glosas_lancadas', 0)), int(dados.get('apostilamentos_bancarios', 0)))
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('''INSERT INTO lancamentos_remessas (data_pagamento, nome_remessa, qtd_fornecedores, qtd_processos, qtd_contratos, certidoes_renovadas, pagamentos_parciais, glosas_lancadas, apostilamentos_bancarios, pontuacao_total, matricula_usuario) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (dados.get('data_pagamento'), dados.get('nome_remessa'), int(dados.get('qtd_fornecedores', 0)), int(dados.get('qtd_processos', 0)), int(dados.get('qtd_contratos', 0)), int(dados.get('certidoes_renovadas', 0)), int(dados.get('pagamentos_parciais', 0)), int(dados.get('glosas_lancadas', 0)), int(dados.get('apostilamentos_bancarios', 0)), pontuacao, matricula))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 201

@app.route('/api/atualizar-lote/<int:id_remessa>', methods=['PUT'])
def atualizar_lote_remessa(id_remessa):
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    dados = request.json
    pontuacao = calcular_esforco(int(dados.get('qtd_processos', 0)), int(dados.get('qtd_contratos', 0)), int(dados.get('certidoes_renovadas', 0)), int(dados.get('pagamentos_parciais', 0)), int(dados.get('glosas_lancadas', 0)), int(dados.get('apostilamentos_bancarios', 0)))
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('''UPDATE lancamentos_remessas SET data_pagamento = ?, nome_remessa = ?, qtd_fornecedores = ?, qtd_processos = ?, qtd_contratos = ?, certidoes_renovadas = ?, pagamentos_parciais = ?, glosas_lancadas = ?, apostilamentos_bancarios = ?, pontuacao_total = ? WHERE id = ? AND matricula_usuario = ?''', (dados.get('data_pagamento'), dados.get('nome_remessa'), int(dados.get('qtd_fornecedores', 0)), int(dados.get('qtd_processos', 0)), int(dados.get('qtd_contratos', 0)), int(dados.get('certidoes_renovadas', 0)), int(dados.get('pagamentos_parciais', 0)), int(dados.get('glosas_lancadas', 0)), int(dados.get('apostilamentos_bancarios', 0)), pontuacao, id_remessa, session['usuario']))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 200

@app.route('/api/listar-remessas', methods=['GET'])
def listar_remessas():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    matricula = session['usuario']
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row  
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM lancamentos_remessas WHERE matricula_usuario = ? ORDER BY id DESC', (matricula,))
    linhas = cursor.fetchall()
    resultado = [{"id": r["id"], "data_pagamento": r["data_pagamento"], "nome_remessa": r["nome_remessa"], "qtd_fornecedores": r["qtd_fornecedores"], "qtd_processos": r["qtd_processos"], "qtd_contratos": r["qtd_contratos"], "certidoes_renovadas": r["certidoes_renovadas"], "pagamentos_parciais": r["pagamentos_parciais"], "glosas_lancadas": r["glosas_lancadas"] if "glosas_lancadas" in r.keys() else 0, "apostilamentos_bancarios": r["apostilamentos_bancarios"] if "apostilamentos_bancarios" in r.keys() else 0, "pontuacao_total": r["pontuacao_total"]} for r in linhas]
    conexao.close()
    return jsonify(resultado), 200

@app.route('/api/deletar-lote/<int:id_remessa>', methods=['DELETE'])
def deletar_lote_remessa(id_remessa):
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM lancamentos_remessas WHERE id = ? AND matricula_usuario = ?', (id_remessa, session['usuario']))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 200

@app.route('/api/salvar-ocorrencia', methods=['POST'])
def salvar_ocorrencia():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    dados = request.json
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('INSERT INTO ocorrencias (data_registro, motivo, referencia, tempo_impacto, observacoes, matricula_usuario) VALUES (?, ?, ?, ?, ?, ?)', (dados.get('data_registro'), dados.get('motivo'), dados.get('referencia', ''), float(dados.get('tempo_impacto', 0)), dados.get('observacoes', ''), session['usuario']))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 201

@app.route('/api/atualizar-ocorrencia/<int:id_oco>', methods=['PUT'])
def atualizar_ocorrencia(id_oco):
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    dados = request.json
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('UPDATE ocorrencias SET data_registro = ?, motivo = ?, referencia = ?, tempo_impacto = ?, observacoes = ? WHERE id = ? AND matricula_usuario = ?', (dados.get('data_registro'), dados.get('motivo'), dados.get('referencia', ''), float(dados.get('tempo_impacto', 0)), dados.get('observacoes', ''), id_oco, session['usuario']))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 200

@app.route('/api/listar-ocorrencias', methods=['GET'])
def listar_ocorrencias():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row  
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM ocorrencias WHERE matricula_usuario = ? ORDER BY id DESC', (session['usuario'],))
    linhas = cursor.fetchall()
    resultado = [{"id": r["id"], "data_registro": r["data_registro"], "motivo": r["motivo"], "referencia": r["referencia"], "tempo_impacto": r["tempo_impacto"], "observacoes": r["observacoes"]} for r in linhas]
    conexao.close()
    return jsonify(resultado), 200

@app.route('/api/deletar-ocorrencia/<int:id_oco>', methods=['DELETE'])
def deletar_ocorrencia(id_oco):
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM ocorrencias WHERE id = ? AND matricula_usuario = ?', (id_oco, session['usuario']))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
