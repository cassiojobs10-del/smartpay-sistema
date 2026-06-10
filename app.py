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

def calcular_esforco(processos, contratos, certidoes, parciais):
    return (processos * 1) + (contratos * 2) + (certidoes * 1) + (parciais * 2)

# Rota para exibir a interface visual
@app.route('/')
def index():
    return render_template('index.html')

# Rota para salvar os dados
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

if __name__ == '__main__':
    inicializar_banco_dados()
    # Usa a porta definida pelo Render ou 5000 como padrão
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
