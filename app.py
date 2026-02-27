import os
import psycopg2
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, connect_timeout=5)

# ==================================================
# HOME
# ==================================================
@app.route("/")
def home():
    return redirect("/tipos")

# ==================================================
# TIPOS DE ATIVOS
# ==================================================
@app.route("/tipos", methods=["GET", "POST"])
def tipos():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        descricao = request.form["descricao"]
        cur.execute("INSERT INTO tipos_ativos (descricao) VALUES (%s)", (descricao,))
        conn.commit()

    cur.execute("SELECT * FROM tipos_ativos ORDER BY id")
    tipos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("tipos_ativos.html", tipos=tipos)

# ==================================================
# ATIVOS
# ==================================================
@app.route("/ativos", methods=["GET", "POST"])
def ativos():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        ticker = request.form["ticker"]
        nome = request.form["nome"]
        tipo_id = request.form["tipo_id"]

        cur.execute("""
            INSERT INTO ativos (ticker, nome, tipo_id)
            VALUES (%s, %s, %s)
        """, (ticker, nome, tipo_id))
        conn.commit()

    cur.execute("SELECT * FROM tipos_ativos")
    tipos = cur.fetchall()

    cur.execute("""
        SELECT a.id, a.ticker, a.nome, t.descricao
        FROM ativos a
        JOIN tipos_ativos t ON a.tipo_id = t.id
        ORDER BY a.id
    """)
    ativos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("ativos.html", ativos=ativos, tipos=tipos)

# ==================================================
# APORTES
# ==================================================
@app.route("/aportes", methods=["GET", "POST"])
def aportes():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO aportes (ativo_id, data_aporte, quantidade, valor_unitario)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["ativo_id"],
            request.form["data_aporte"],
            request.form["quantidade"],
            request.form["valor_unitario"]
        ))
        conn.commit()

    cur.execute("SELECT id, ticker FROM ativos")
    ativos = cur.fetchall()

    cur.execute("""
        SELECT a.ticker, ap.data_aporte, ap.quantidade, ap.valor_unitario
        FROM aportes ap
        JOIN ativos a ON ap.ativo_id = a.id
        ORDER BY ap.id DESC
    """)
    aportes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("aportes.html", aportes=aportes, ativos=ativos)

# ==================================================
# DIVIDENDOS
# ==================================================
@app.route("/dividendos", methods=["GET", "POST"])
def dividendos():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO dividendos (ativo_id, data_pagamento, valor_recebido)
            VALUES (%s, %s, %s)
        """, (
            request.form["ativo_id"],
            request.form["data_pagamento"],
            request.form["valor_recebido"]
        ))
        conn.commit()

    cur.execute("SELECT id, ticker FROM ativos")
    ativos = cur.fetchall()

    cur.execute("""
        SELECT a.ticker, d.data_pagamento, d.valor_recebido
        FROM dividendos d
        JOIN ativos a ON d.ativo_id = a.id
        ORDER BY d.id DESC
    """)
    dividendos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dividendos.html", dividendos=dividendos, ativos=ativos)

# ==================================================
# CATEGORIAS
# ==================================================
@app.route("/categorias", methods=["GET", "POST"])
def categorias():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO categorias_financeiras (descricao, tipo)
            VALUES (%s, %s)
        """, (
            request.form["descricao"],
            request.form["tipo"]
        ))
        conn.commit()

    cur.execute("SELECT * FROM categorias_financeiras ORDER BY id")
    categorias = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("categorias.html", categorias=categorias)

# ==================================================
# MOVIMENTAÇÕES
# ==================================================
@app.route("/movimentacoes", methods=["GET", "POST"])
def movimentacoes():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO movimentacoes_financeiras
            (data_movimento, categoria_id, valor, descricao)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["data_movimento"],
            request.form["categoria_id"],
            request.form["valor"],
            request.form["descricao"]
        ))
        conn.commit()

    cur.execute("SELECT id, descricao, tipo FROM categorias_financeiras")
    categorias = cur.fetchall()

    cur.execute("""
        SELECT m.data_movimento, c.descricao, c.tipo, m.valor, m.descricao
        FROM movimentacoes_financeiras m
        JOIN categorias_financeiras c ON m.categoria_id = c.id
        ORDER BY m.id DESC
    """)
    movimentacoes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("movimentacoes.html", movimentacoes=movimentacoes, categorias=categorias)

# ==================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
	