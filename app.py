from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
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
            pontuacao_total INTEGER NOT NULL,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conexao.commit()
    conexao.close()

# A SOLUÇÃO ESTÁ AQUI:
# Chamamos a função logo na raiz do código. Assim, o Gunicorn do Render 
# é forçado a criar o banco de dados antes de processar qualquer coisa.
inicializar_banco_dados()

def calcular_esforco(processos, contratos, certidoes, parciais):
    return (processos * 1) + (contratos * 2) + (certidoes * 1) + (parciais * 2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/salvar-lote', methods=['POST'])
def salvar_lote_remessa():
    dados = request.json
    try:
        data_pagamento = dados.get('data_pagamento')
        nome_remessa = dados.get('nome_remessa')
        qtd_fornecedores = int(dados.get('qtd_fornecedores', 0))
        qtd_processos = int(dados.get('qtd_processos', 0))
        qtd_contratos = int(dados.get('qtd_contratos', 0))
        certidoes_renovadas = int(dados.get('certidoes_renovadas', 0))
        pagamentos_parciais = int(dados.get('pagamentos_parciais', 0))

        pontuacao_final = calcular_esforco(
            qtd_processos, qtd_contratos, certidoes_renovadas, pagamentos_parciais
        )

        conexao = sqlite3.connect(NOME_BANCO)
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO lancamentos_remessas 
            (data_pagamento, nome_remessa, qtd_fornecedores, qtd_processos, 
            qtd_contratos, certidoes_renovadas, pagamentos_parciais, pontuacao_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data_pagamento, nome_remessa, qtd_fornecedores, qtd_processos, 
              qtd_contratos, certidoes_renovadas, pagamentos_parciais, pontuacao_final))
        
        conexao.commit()
        conexao.close()

        return jsonify({"status": "sucesso", "pontos": pontuacao_final}), 201

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400

@app.route('/api/listar-remessas', methods=['GET'])
def listar_remessas():
    try:
        conexao = sqlite3.connect(NOME_BANCO)
        conexao.row_factory = sqlite3.Row  
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM lancamentos_remessas ORDER BY id DESC')
        linhas = cursor.fetchall()
        
        resultado = []
        for linha in linhas:
            resultado.append({
                "id": linha["id"],
                "data_pagamento": linha["data_pagamento"],
                "nome_remessa": linha["nome_remessa"],
                "qtd_fornecedores": linha["qtd_fornecedores"],
                "qtd_processos": linha["qtd_processos"],
                "qtd_contratos": linha["qtd_contratos"],
                "certidoes_renovadas": linha["certidoes_renovadas"],
                "pagamentos_parciais": linha["pagamentos_parciais"],
                "pontuacao_total": linha["pontuacao_total"]
            })
        
        conexao.close()
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    # ROTA 3: Atualizar Lote (Edição)
@app.route('/api/atualizar-lote/<int:id_remessa>', methods=['PUT'])
def atualizar_lote_remessa(id_remessa):
    dados = request.json
    try:
        data_pagamento = dados.get('data_pagamento')
        nome_remessa = dados.get('nome_remessa')
        qtd_fornecedores = int(dados.get('qtd_fornecedores', 0))
        qtd_processos = int(dados.get('qtd_processos', 0))
        qtd_contratos = int(dados.get('qtd_contratos', 0))
        certidoes_renovadas = int(dados.get('certidoes_renovadas', 0))
        pagamentos_parciais = int(dados.get('pagamentos_parciais', 0))

        pontuacao_final = calcular_esforco(
            qtd_processos, qtd_contratos, certidoes_renovadas, pagamentos_parciais
        )

        conexao = sqlite3.connect(NOME_BANCO)
        cursor = conexao.cursor()
        cursor.execute('''
            UPDATE lancamentos_remessas 
            SET data_pagamento = ?, nome_remessa = ?, qtd_fornecedores = ?, 
                qtd_processos = ?, qtd_contratos = ?, certidoes_renovadas = ?, 
                pagamentos_parciais = ?, pontuacao_total = ?
            WHERE id = ?
        ''', (data_pagamento, nome_remessa, qtd_fornecedores, qtd_processos, 
              qtd_contratos, certidoes_renovadas, pagamentos_parciais, pontuacao_final, id_remessa))
        
        conexao.commit()
        conexao.close()

        return jsonify({"status": "sucesso", "pontos": pontuacao_final}), 200

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
