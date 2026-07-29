from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "vortasky_secret_key_produtividade"

# Garante que o arquivo do banco de dados seja criado na pasta raiz absoluta do app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOME_BANCO = os.path.join(BASE_DIR, "smartpay_produtividade.db")

def obter_conexao():
    conexao = sqlite3.connect(NOME_BANCO, timeout=20.0)
    # Força a gravação imediata e direta no arquivo físico (evita perda de dados em cache)
    conexao.execute("PRAGMA synchronous = FULL")
    conexao.execute("PRAGMA journal_mode = DELETE")
    return conexao

def inicializar_banco_dados():
    conexao = obter_conexao()
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
    
    # GARANTE QUE O ADMIN SUPREMO (CÁSSIO) ESTÁ SEMPRE PRESENTE E PROTEGIDO
    cursor.execute('SELECT COUNT(*) FROM colaboradores WHERE matricula = "12345"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin)
            VALUES ('12345', 'Cássio Abreu', 'Gestor Financeiro', '30/12/95', 1)
        ''')
    else:
        cursor.execute('UPDATE colaboradores SET is_admin = 1 WHERE matricula = "12345"')
        
    conexao.commit()
    conexao.close()

inicializar_banco_dados()
