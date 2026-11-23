import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sgp-smartpay-chave-secreta-2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpay_produtividade.db")

ADMIN_MATRICULA_SUPREMA = "12345"
ADMIN_NOME_SUPREMO = "Cássio Abreu"
ADMIN_SENHA_SUPREMA = "30/12/95"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA synchronous = FULL")
    conn.execute("PRAGMA journal_mode = DELETE")
    return conn


def calcular_esforco(
    processos, contratos, certidoes, parciais, glosas, apostilamentos
):
    return (
        (int(processos or 0) * 1)
        + (int(contratos or 0) * 2)
        + (int(certidoes or 0) * 1)
        + (int(parciais or 0) * 1)
        + (int(glosas or 0) * 1)
        + (int(apostilamentos or 0) * 2)
    )


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS colaboradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                cargo TEXT NOT NULL DEFAULT 'Analista',
                data_nascimento TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lancamentos_remessas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_pagamento TEXT NOT NULL,
                nome_remessa TEXT NOT NULL,
                qtd_fornecedores INTEGER NOT NULL DEFAULT 0,
                qtd_processos INTEGER NOT NULL DEFAULT 0,
                qtd_contratos INTEGER NOT NULL DEFAULT 0,
                certidoes_renovadas INTEGER NOT NULL DEFAULT 0,
                pagamentos_parciais INTEGER NOT NULL DEFAULT 0,
                glosas_lancadas INTEGER NOT NULL DEFAULT 0,
                apostilamentos_bancarios INTEGER NOT NULL DEFAULT 0,
                pontuacao_total INTEGER NOT NULL DEFAULT 0,
                data_registro TEXT NOT NULL,
                matricula_usuario TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ocorrencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_registro TEXT NOT NULL,
                motivo TEXT NOT NULL,
                referencia TEXT NOT NULL,
                tempo_impacto REAL NOT NULL DEFAULT 0,
                observacoes TEXT DEFAULT '',
                matricula_usuario TEXT NOT NULL,
                data_criacao TEXT NOT NULL
            )
            """
        )

        # Garante sempre a existência e integridade do Administrador Supremo
        admin_existente = conn.execute(
            "SELECT id FROM colaboradores WHERE matricula = ?",
            (ADMIN_MATRICULA_SUPREMA,),
        ).fetchone()

        if not admin_existente:
            conn.execute(
                """
                INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin)
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    ADMIN_MATRICULA_SUPREMA,
                    ADMIN_NOME_SUPREMO,
                    "Administrador Supremo",
                    ADMIN_SENHA_SUPREMA,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE colaboradores
                SET nome = COALESCE(NULLIF(nome, ''), ?),
                    data_nascimento = COALESCE(NULLIF(data_nascimento, ''), ?),
                    is_admin = 1
                WHERE matricula = ?
                """,
                (ADMIN_NOME_SUPREMO, ADMIN_SENHA_SUPREMA, ADMIN_MATRICULA_SUPREMA),
            )

        conn.commit()


init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "matricula" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"erro": "Não autenticado."}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "matricula" not in session:
            return jsonify({"erro": "Não autenticado."}), 401
        if not session.get("is_admin"):
            return jsonify({"erro": "Acesso restrito a administradores."}), 403
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "matricula" in session:
            return redirect(url_for("index"))
        return render_template("login.html")

    data = request.get_json(silent=True) or {}
    usuario = str(data.get("usuario", "")).strip()
    senha = str(data.get("senha", "")).strip()

    if not usuario or not senha:
        return (
            jsonify(
                {
                    "status": "erro",
                    "mensagem": "Informe a matrícula e a senha.",
                }
            ),
            400,
        )

    with get_db_connection() as conn:
        user = conn.execute(
            """
            SELECT matricula, nome, cargo, data_nascimento, is_admin
            FROM colaboradores
            WHERE matricula = ?
            """,
            (usuario,),
        ).fetchone()

    if not user or user["data_nascimento"].strip() != senha:
        return (
            jsonify(
                {
                    "status": "erro",
                    "mensagem": "Matrícula ou data de nascimento incorretos.",
                }
            ),
            401,
        )

    is_supremo = user["matricula"] == ADMIN_MATRICULA_SUPREMA
    session.clear()
    session["matricula"] = user["matricula"]
    session["nome"] = ADMIN_NOME_SUPREMO if is_supremo else user["nome"]
    session["cargo"] = user["cargo"]
    session["is_admin"] = 1 if (is_supremo or int(user["is_admin"]) == 1) else 0

    return jsonify({"status": "sucesso", "redirect": url_for("index")})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        usuario_matricula=session.get("matricula"),
        usuario_nome=session.get("nome"),
        usuario_cargo=session.get("cargo"),
        is_admin=bool(session.get("is_admin")),
    )


@app.route("/api/sessao", methods=["GET"])
@login_required
def api_sessao():
    return jsonify(
        {
            "matricula": session.get("matricula"),
            "nome": session.get("nome"),
            "cargo": session.get("cargo"),
            "is_admin": bool(session.get("is_admin")),
        }
    )


# ==========================================================
# REMESSAS PAGAS (CRUD COM ISOLAMENTO POR MATRÍCULA)
# ==========================================================
@app.route("/api/remessas", methods=["GET", "POST"])
@login_required
def api_remessas():
    matricula_atual = session.get("matricula")
    is_admin = bool(session.get("is_admin"))

    with get_db_connection() as conn:
        if request.method == "GET":
            filtro_matricula = request.args.get("matricula", "").strip()

            if is_admin:
                if filtro_matricula and filtro_matricula != "TODOS":
                    rows = conn.execute(
                        """
                        SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
                        FROM lancamentos_remessas r
                        LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
                        WHERE r.matricula_usuario = ?
                        ORDER BY r.id DESC
                        """,
                        (filtro_matricula,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
                        FROM lancamentos_remessas r
                        LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
                        ORDER BY r.id DESC
                        """
                    ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
                    FROM lancamentos_remessas r
                    LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
                    WHERE r.matricula_usuario = ?
                    ORDER BY r.id DESC
                    """,
                    (matricula_atual,),
                ).fetchall()

            return jsonify([dict(row) for row in rows])

        data = request.get_json(silent=True) or {}
        data_pagamento = str(data.get("data_pagamento", "")).strip()
        nome_remessa = str(data.get("nome_remessa", "")).strip()

        if not data_pagamento or not nome_remessa:
            return (
                jsonify(
                    {
                        "erro": "Data de pagamento e nome da remessa são obrigatórios."
                    }
                ),
                400,
            )

        fornecedores = int(data.get("qtd_fornecedores", 0) or 0)
        processos = int(data.get("qtd_processos", 0) or 0)
        contratos = int(data.get("qtd_contratos", 0) or 0)
        certidoes = int(data.get("certidoes_renovadas", 0) or 0)
        parciais = int(data.get("pagamentos_parciais", 0) or 0)
        glosas = int(data.get("glosas_lancadas", 0) or 0)
        apostilamentos = int(data.get("apostilamentos_bancarios", 0) or 0)

        pontuacao = calcular_esforco(
            processos, contratos, certidoes, parciais, glosas, apostilamentos
        )
        data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = conn.execute(
            """
            INSERT INTO lancamentos_remessas (
                data_pagamento, nome_remessa, qtd_fornecedores, qtd_processos,
                qtd_contratos, certidoes_renovadas, pagamentos_parciais,
                glosas_lancadas, apostilamentos_bancarios, pontuacao_total,
                data_registro, matricula_usuario
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data_pagamento,
                nome_remessa,
                fornecedores,
                processos,
                contratos,
                certidoes,
                parciais,
                glosas,
                apostilamentos,
                pontuacao,
                data_registro,
                matricula_atual,
            ),
        )
        conn.commit()

        novo = conn.execute(
            """
            SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
            FROM lancamentos_remessas r
            LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
            WHERE r.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(dict(novo)), 201


@app.route("/api/remessas/<int:remessa_id>", methods=["PUT", "DELETE"])
@login_required
def api_remessa_item(remessa_id):
    matricula_atual = session.get("matricula")
    is_admin = bool(session.get("is_admin"))

    with get_db_connection() as conn:
        registro = conn.execute(
            "SELECT * FROM lancamentos_remessas WHERE id = ?", (remessa_id,)
        ).fetchone()

        if not registro:
            return jsonify({"erro": "Registro de remessa não encontrado."}), 404

        if not is_admin and registro["matricula_usuario"] != matricula_atual:
            return (
                jsonify(
                    {
                        "erro": "Você não tem permissão para alterar ou excluir este registro."
                    }
                ),
                403,
            )

        if request.method == "DELETE":
            conn.execute(
                "DELETE FROM lancamentos_remessas WHERE id = ?", (remessa_id,)
            )
            conn.commit()
            return jsonify({"status": "excluido", "id": remessa_id})

        data = request.get_json(silent=True) or {}
        data_pagamento = str(
            data.get("data_pagamento", registro["data_pagamento"])
        ).strip()
        nome_remessa = str(
            data.get("nome_remessa", registro["nome_remessa"])
        ).strip()
        fornecedores = int(
            data.get("qtd_fornecedores", registro["qtd_fornecedores"]) or 0
        )
        processos = int(
            data.get("qtd_processos", registro["qtd_processos"]) or 0
        )
        contratos = int(
            data.get("qtd_contratos", registro["qtd_contratos"]) or 0
        )
        certidoes = int(
            data.get("certidoes_renovadas", registro["certidoes_renovadas"])
            or 0
        )
        parciais = int(
            data.get("pagamentos_parciais", registro["pagamentos_parciais"])
            or 0
        )
        glosas = int(
            data.get("glosas_lancadas", registro["glosas_lancadas"]) or 0
        )
        apostilamentos = int(
            data.get(
                "apostilamentos_bancarios", registro["apostilamentos_bancarios"]
            )
            or 0
        )

        pontuacao = calcular_esforco(
            processos, contratos, certidoes, parciais, glosas, apostilamentos
        )

        conn.execute(
            """
            UPDATE lancamentos_remessas
            SET data_pagamento = ?,
                nome_remessa = ?,
                qtd_fornecedores = ?,
                qtd_processos = ?,
                qtd_contratos = ?,
                certidoes_renovadas = ?,
                pagamentos_parciais = ?,
                glosas_lancadas = ?,
                apostilamentos_bancarios = ?,
                pontuacao_total = ?
            WHERE id = ?
            """,
            (
                data_pagamento,
                nome_remessa,
                fornecedores,
                processos,
                contratos,
                certidoes,
                parciais,
                glosas,
                apostilamentos,
                pontuacao,
                remessa_id,
            ),
        )
        conn.commit()

        atualizado = conn.execute(
            """
            SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
            FROM lancamentos_remessas r
            LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
            WHERE r.id = ?
            """,
            (remessa_id,),
        ).fetchone()
        return jsonify(dict(atualizado))


# ==========================================================
# OCORRÊNCIAS / PENDÊNCIAS (CRUD COM ISOLAMENTO POR MATRÍCULA)
# ==========================================================
@app.route("/api/ocorrencias", methods=["GET", "POST"])
@login_required
def api_ocorrencias():
    matricula_atual = session.get("matricula")
    is_admin = bool(session.get("is_admin"))

    with get_db_connection() as conn:
        if request.method == "GET":
            filtro_matricula = request.args.get("matricula", "").strip()

            if is_admin:
                if filtro_matricula and filtro_matricula != "TODOS":
                    rows = conn.execute(
                        """
                        SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
                        FROM ocorrencias o
                        LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
                        WHERE o.matricula_usuario = ?
                        ORDER BY o.id DESC
                        """,
                        (filtro_matricula,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
                        FROM ocorrencias o
                        LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
                        ORDER BY o.id DESC
                        """
                    ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
                    FROM ocorrencias o
                    LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
                    WHERE o.matricula_usuario = ?
                    ORDER BY o.id DESC
                    """,
                    (matricula_atual,),
                ).fetchall()

            return jsonify([dict(row) for row in rows])

        data = request.get_json(silent=True) or {}
        data_registro = str(data.get("data_registro", "")).strip()
        motivo = str(data.get("motivo", "")).strip()
        referencia = str(data.get("referencia", "")).strip()
        tempo_impacto = float(data.get("tempo_impacto", 0) or 0)
        observacoes = str(data.get("observacoes", "")).strip()

        if not data_registro or not motivo or not referencia:
            return (
                jsonify(
                    {
                        "erro": "Data, motivo e referência são obrigatórios."
                    }
                ),
                400,
            )

        data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """
            INSERT INTO ocorrencias (
                data_registro, motivo, referencia, tempo_impacto,
                observacoes, matricula_usuario, data_criacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data_registro,
                motivo,
                referencia,
                tempo_impacto,
                observacoes,
                matricula_atual,
                data_criacao,
            ),
        )
        conn.commit()

        nova = conn.execute(
            """
            SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
            FROM ocorrencias o
            LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
            WHERE o.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(dict(nova)), 201


@app.route("/api/ocorrencias/<int:ocorrencia_id>", methods=["PUT", "DELETE"])
@login_required
def api_ocorrencia_item(ocorrencia_id):
    matricula_atual = session.get("matricula")
    is_admin = bool(session.get("is_admin"))

    with get_db_connection() as conn:
        registro = conn.execute(
            "SELECT * FROM ocorrencias WHERE id = ?", (ocorrencia_id,)
        ).fetchone()

        if not registro:
            return jsonify({"erro": "Ocorrência não encontrada."}), 404

        if not is_admin and registro["matricula_usuario"] != matricula_atual:
            return (
                jsonify(
                    {
                        "erro": "Você não tem permissão para alterar ou excluir esta ocorrência."
                    }
                ),
                403,
            )

        if request.method == "DELETE":
            conn.execute(
                "DELETE FROM ocorrencias WHERE id = ?", (ocorrencia_id,)
            )
            conn.commit()
            return jsonify({"status": "excluido", "id": ocorrencia_id})

        data = request.get_json(silent=True) or {}
        data_registro = str(
            data.get("data_registro", registro["data_registro"])
        ).strip()
        motivo = str(data.get("motivo", registro["motivo"])).strip()
        referencia = str(
            data.get("referencia", registro["referencia"])
        ).strip()
        tempo_impacto = float(
            data.get("tempo_impacto", registro["tempo_impacto"]) or 0
        )
        observacoes = str(
            data.get("observacoes", registro["observacoes"])
        ).strip()

        conn.execute(
            """
            UPDATE ocorrencias
            SET data_registro = ?,
                motivo = ?,
                referencia = ?,
                tempo_impacto = ?,
                observacoes = ?
            WHERE id = ?
            """,
            (
                data_registro,
                motivo,
                referencia,
                tempo_impacto,
                observacoes,
                ocorrencia_id,
            ),
        )
        conn.commit()

        atualizada = conn.execute(
            """
            SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
            FROM ocorrencias o
            LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
            WHERE o.id = ?
            """,
            (ocorrencia_id,),
        ).fetchone()
        return jsonify(dict(atualizada))


# ==========================================================
# GESTÃO DE COLABORADORES (APENAS ADMIN + BLINDAGEM DO 12345)
# ==========================================================
@app.route("/api/colaboradores", methods=["GET", "POST"])
@login_required
@admin_required
def api_colaboradores():
    with get_db_connection() as conn:
        if request.method == "GET":
            rows = conn.execute(
                """
                SELECT id, matricula, nome, cargo, data_nascimento, is_admin
                FROM colaboradores
                ORDER BY is_admin DESC, nome ASC
                """
            ).fetchall()
            return jsonify([dict(row) for row in rows])

        data = request.get_json(silent=True) or {}
        matricula = str(data.get("matricula", "")).strip()
        nome = str(data.get("nome", "")).strip()
        cargo = str(data.get("cargo", "Analista")).strip() or "Analista"
        data_nascimento = str(data.get("data_nascimento", "")).strip()
        is_admin_novo = 1 if int(data.get("is_admin", 0) or 0) == 1 else 0

        if not matricula or not nome or not data_nascimento:
            return (
                jsonify(
                    {
                        "erro": "Matrícula, nome e data de nascimento são obrigatórios."
                    }
                ),
                400,
            )

        if matricula == ADMIN_MATRICULA_SUPREMA:
            is_admin_novo = 1

        try:
            cursor = conn.execute(
                """
                INSERT INTO colaboradores (matricula, nome, cargo, data_nascimento, is_admin)
                VALUES (?, ?, ?, ?, ?)
                """,
                (matricula, nome, cargo, data_nascimento, is_admin_novo),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return (
                jsonify({"erro": "Já existe um colaborador com essa matrícula."}),
                409,
            )

        novo = conn.execute(
            """
            SELECT id, matricula, nome, cargo, data_nascimento, is_admin
            FROM colaboradores
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(dict(novo)), 201


@app.route("/api/colaboradores/<int:colab_id>", methods=["PUT", "DELETE"])
@login_required
@admin_required
def api_colaborador_item(colab_id):
    with get_db_connection() as conn:
        colab = conn.execute(
            "SELECT * FROM colaboradores WHERE id = ?", (colab_id,)
        ).fetchone()

        if not colab:
            return jsonify({"erro": "Colaborador não encontrado."}), 404

        if colab["matricula"] == ADMIN_MATRICULA_SUPREMA:
            if request.method == "DELETE":
                return (
                    jsonify(
                        {
                            "erro": "A conta do Administrador Supremo não pode ser excluída."
                        }
                    ),
                    403,
                )

            data = request.get_json(silent=True) or {}
            nome = str(data.get("nome", colab["nome"])).strip() or colab["nome"]
            cargo = str(data.get("cargo", colab["cargo"])).strip() or colab["cargo"]
            data_nascimento = (
                str(data.get("data_nascimento", colab["data_nascimento"])).strip()
                or colab["data_nascimento"]
            )

            conn.execute(
                """
                UPDATE colaboradores
                SET nome = ?, cargo = ?, data_nascimento = ?, is_admin = 1
                WHERE id = ?
                """,
                (nome, cargo, data_nascimento, colab_id),
            )
            conn.commit()
            atualizado = conn.execute(
                """
                SELECT id, matricula, nome, cargo, data_nascimento, is_admin
                FROM colaboradores
                WHERE id = ?
                """,
                (colab_id,),
            ).fetchone()
            return jsonify(dict(atualizado))

        if request.method == "DELETE":
            conn.execute("DELETE FROM colaboradores WHERE id = ?", (colab_id,))
            conn.commit()
            return jsonify({"status": "excluido", "id": colab_id})

        data = request.get_json(silent=True) or {}
        nome = str(data.get("nome", colab["nome"])).strip() or colab["nome"]
        cargo = str(data.get("cargo", colab["cargo"])).strip() or colab["cargo"]
        data_nascimento = (
            str(data.get("data_nascimento", colab["data_nascimento"])).strip()
            or colab["data_nascimento"]
        )
        is_admin_atualizado = (
            1 if int(data.get("is_admin", colab["is_admin"]) or 0) == 1 else 0
        )

        conn.execute(
            """
            UPDATE colaboradores
            SET nome = ?, cargo = ?, data_nascimento = ?, is_admin = ?
            WHERE id = ?
            """,
            (nome, cargo, data_nascimento, is_admin_atualizado, colab_id),
        )
        conn.commit()

        atualizado = conn.execute(
            """
            SELECT id, matricula, nome, cargo, data_nascimento, is_admin
            FROM colaboradores
            WHERE id = ?
            """,
            (colab_id,),
        ).fetchone()
        return jsonify(dict(atualizado))


# ==========================================================
# RELATÓRIOS & BI
# ==========================================================
@app.route("/api/bi", methods=["GET"])
@login_required
def api_bi():
    matricula_atual = session.get("matricula")
    is_admin = bool(session.get("is_admin"))
    filtro_matricula = request.args.get("matricula", "").strip()

    with get_db_connection() as conn:
        if is_admin:
            colaboradores_rows = conn.execute(
                "SELECT matricula, nome, cargo, is_admin FROM colaboradores ORDER BY nome ASC"
            ).fetchall()
            colaboradores_lista = [dict(c) for c in colaboradores_rows]

            if filtro_matricula and filtro_matricula != "TODOS":
                remessas = conn.execute(
                    """
                    SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
                    FROM lancamentos_remessas r
                    LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
                    WHERE r.matricula_usuario = ?
                    ORDER BY r.id DESC
                    """,
                    (filtro_matricula,),
                ).fetchall()
                ocorrencias = conn.execute(
                    """
                    SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
                    FROM ocorrencias o
                    LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
                    WHERE o.matricula_usuario = ?
                    ORDER BY o.id DESC
                    """,
                    (filtro_matricula,),
                ).fetchall()
            else:
                remessas = conn.execute(
                    """
                    SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
                    FROM lancamentos_remessas r
                    LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
                    ORDER BY r.id DESC
                    """
                ).fetchall()
                ocorrencias = conn.execute(
                    """
                    SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
                    FROM ocorrencias o
                    LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
                    ORDER BY o.id DESC
                    """
                ).fetchall()
        else:
            meu_colab = conn.execute(
                "SELECT matricula, nome, cargo, is_admin FROM colaboradores WHERE matricula = ?",
                (matricula_atual,),
            ).fetchone()
            colaboradores_lista = [dict(meu_colab)] if meu_colab else []

            remessas = conn.execute(
                """
                SELECT r.*, COALESCE(c.nome, r.matricula_usuario) AS nome_colaborador
                FROM lancamentos_remessas r
                LEFT JOIN colaboradores c ON c.matricula = r.matricula_usuario
                WHERE r.matricula_usuario = ?
                ORDER BY r.id DESC
                """,
                (matricula_atual,),
            ).fetchall()
            ocorrencias = conn.execute(
                """
                SELECT o.*, COALESCE(c.nome, o.matricula_usuario) AS nome_colaborador
                FROM ocorrencias o
                LEFT JOIN colaboradores c ON c.matricula = o.matricula_usuario
                WHERE o.matricula_usuario = ?
                ORDER BY o.id DESC
                """,
                (matricula_atual,),
            ).fetchall()

        remessas_list = [dict(r) for r in remessas]
        ocorrencias_list = [dict(o) for o in ocorrencias]

        total_pontos = sum(int(r["pontuacao_total"] or 0) for r in remessas_list)
        total_remessas = len(remessas_list)
        total_processos = sum(int(r["qtd_processos"] or 0) for r in remessas_list)
        total_contratos = sum(int(r["qtd_contratos"] or 0) for r in remessas_list)
        total_ocorrencias = len(ocorrencias_list)
        total_horas_paradas = round(
            sum(float(o["tempo_impacto"] or 0) for o in ocorrencias_list), 2
        )

        # Agrupamento por colaborador (drill-down)
        mapa_colab = {}
        for r in remessas_list:
            mat = r["matricula_usuario"]
            if mat not in mapa_colab:
                mapa_colab[mat] = {
                    "matricula": mat,
                    "nome": r["nome_colaborador"],
                    "pontos": 0,
                    "remessas": 0,
                    "processos": 0,
                    "contratos": 0,
                    "ocorrencias": 0,
                    "horas_paradas": 0.0,
                }
            mapa_colab[mat]["pontos"] += int(r["pontuacao_total"] or 0)
            mapa_colab[mat]["remessas"] += 1
            mapa_colab[mat]["processos"] += int(r["qtd_processos"] or 0)
            mapa_colab[mat]["contratos"] += int(r["qtd_contratos"] or 0)

        for o in ocorrencias_list:
            mat = o["matricula_usuario"]
            if mat not in mapa_colab:
                mapa_colab[mat] = {
                    "matricula": mat,
                    "nome": o["nome_colaborador"],
                    "pontos": 0,
                    "remessas": 0,
                    "processos": 0,
                    "contratos": 0,
                    "ocorrencias": 0,
                    "horas_paradas": 0.0,
                }
            mapa_colab[mat]["ocorrencias"] += 1
            mapa_colab[mat]["horas_paradas"] = round(
                mapa_colab[mat]["horas_paradas"] + float(o["tempo_impacto"] or 0),
                2,
            )

        # Agrupamento por motivo de ocorrência
        mapa_motivos = {}
        for o in ocorrencias_list:
            mot = o["motivo"] or "Outros"
            if mot not in mapa_motivos:
                mapa_motivos[mot] = {"motivo": mot, "quantidade": 0, "horas": 0.0}
            mapa_motivos[mot]["quantidade"] += 1
            mapa_motivos[mot]["horas"] = round(
                mapa_motivos[mot]["horas"] + float(o["tempo_impacto"] or 0), 2
            )

        return jsonify(
            {
                "resumo": {
                    "total_pontos": total_pontos,
                    "total_remessas": total_remessas,
                    "total_processos": total_processos,
                    "total_contratos": total_contratos,
                    "total_ocorrencias": total_ocorrencias,
                    "total_horas_paradas": total_horas_paradas,
                },
                "por_colaborador": list(mapa_colab.values()),
                "por_motivo": list(mapa_motivos.values()),
                "colaboradores": colaboradores_lista,
                "remessas": remessas_list,
                "ocorrencias": ocorrencias_list,
            }
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
