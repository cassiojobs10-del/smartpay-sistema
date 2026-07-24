from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "vortasky_secret_key_produtividade"

NOME_BANCO = "smartpay_produtividade.db"

def inicializar_banco_dados():
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    
    # 1. Tabela de Lançamentos de Remessas
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
            pontuacao_total INTEGER NOT NULL,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Tabela de Colaboradores (Login)
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
    
    # 3. Força a criação do seu usuário Admin padrão (Cássio)
    cursor.execute('SELECT COUNT(*) FROM colaboradores WHERE matricula = "12345"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin)
            VALUES ('12345', 'Cássio Abreu', 'Gestor Financeiro', '30/12/95', 1)
        ''')
        
    conexao.commit()
    conexao.close()

inicializar_banco_dados()

def calcular_esforco(processos, contratos, certidoes, parciais):
    return (processos * 1) + (contratos * 2) + (certidoes * 1) + (parciais * 2)

# ==========================================
# ROTAS DE ACESSO E LOGIN
# ==========================================
@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dados = request.json if request.is_json else request.form
        usuario = dados.get('usuario') # Matrícula
        senha = dados.get('senha')     # Data de Nascimento

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
            
            if request.is_json:
                return jsonify({"status": "sucesso", "redirect": url_for('index')}), 200
            return redirect(url_for('index'))
        else:
            msg_erro = "Matrícula ou data de nascimento incorretos."
            if request.is_json:
                return jsonify({"status": "erro", "mensagem": msg_erro}), 401
            return render_template('login.html', erro=msg_erro)
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# ROTAS DE GESTÃO DE EQUIPE (Somente Admin)
# ==========================================
@app.route('/api/colaboradores', methods=['GET', 'POST'])
def api_colaboradores():
    if 'usuario' not in session or not session.get('is_admin'):
        return jsonify({"status": "erro", "mensagem": "Acesso negado"}), 403
        
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
            is_admin = 1 if dados.get('is_admin') else 0
            cursor.execute('''
                INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (dados['matricula'], dados['nome'], dados['cargo'], dados['data_nascimento'], is_admin))
            conexao.commit()
            conexao.close()
            return jsonify({"status": "sucesso"}), 201
        except sqlite3.IntegrityError:
            conexao.close()
            return jsonify({"status": "erro", "mensagem": "Esta matrícula já está cadastrada."}), 400

@app.route('/api/colaboradores/<int:id_colab>', methods=['DELETE'])
def deletar_colaborador(id_colab):
    if 'usuario' not in session or not session.get('is_admin'):
        return jsonify({"status": "erro", "mensagem": "Acesso negado"}), 403
        
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM colaboradores WHERE id = ?', (id_colab,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 200

# ==========================================
# ROTAS DE REMESSAS (O SEU MOTOR PADRÃO)
# ==========================================
@app.route('/api/metricas-dashboard', methods=['GET'])
def metricas_dashboard():
    if 'usuario' not in session: return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401
    try:
        conexao = sqlite3.connect(NOME_BANCO)
        cursor = conexao.cursor()
        cursor.execute('SELECT TOTAL(pontuacao_total), TOTAL(qtd_processos), COUNT(id) FROM lancamentos_remessas')
        resultado = cursor.fetchone()
        conexao.close()
        return jsonify({
            "pontos_totais": int(resultado[0]) if resultado[0] else 0,
            "processos_totais": int(resultado[1]) if resultado[1] else 0,
            "total_remessas": int(resultado[2]) if resultado[2] else 0
        }), 200
    except Exception as e: return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/salvar-lote', methods=['POST'])
def salvar_lote_remessa():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    dados = request.json
    pontuacao = calcular_esforco(int(dados.get('qtd_processos', 0)), int(dados.get('qtd_contratos', 0)), int(dados.get('certidoes_renovadas', 0)), int(dados.get('pagamentos_parciais', 0)))
    
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('INSERT INTO lancamentos_remessas (data_pagamento, nome_remessa, qtd_fornecedores, qtd_processos, qtd_contratos, certidoes_renovadas, pagamentos_parciais, pontuacao_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                   (dados.get('data_pagamento'), dados.get('nome_remessa'), int(dados.get('qtd_fornecedores', 0)), int(dados.get('qtd_processos', 0)), int(dados.get('qtd_contratos', 0)), int(dados.get('certidoes_renovadas', 0)), int(dados.get('pagamentos_parciais', 0)), pontuacao))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 201

@app.route('/api/listar-remessas', methods=['GET'])
def listar_remessas():
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.row_factory = sqlite3.Row  
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM lancamentos_remessas ORDER BY id DESC')
    linhas = cursor.fetchall()
    resultado = [{"id": r["id"], "data_pagamento": r["data_pagamento"], "nome_remessa": r["nome_remessa"], "qtd_fornecedores": r["qtd_fornecedores"], "qtd_processos": r["qtd_processos"], "pontuacao_total": r["pontuacao_total"]} for r in linhas]
    conexao.close()
    return jsonify(resultado), 200

@app.route('/api/deletar-lote/<int:id_remessa>', methods=['DELETE'])
def deletar_lote_remessa(id_remessa):
    if 'usuario' not in session: return jsonify({"status": "erro"}), 401
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM lancamentos_remessas WHERE id = ?', (id_remessa,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "sucesso"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
