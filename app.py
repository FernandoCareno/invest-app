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
def inicial():
    return render_template("/inicial.html")

# ==================================================
# TIPOS DE ATIVOS (COM FILTRO + NOVO + EDITAR/EXCLUIR)
# ==================================================
@app.route("/tipos", methods=["GET", "POST"])
def tipos():
    conn = get_connection()
    cur = conn.cursor()

    # ---------- POST = NOVO ----------
    if request.method == "POST":
        descricao = request.form["descricao"]

        cur.execute(
            "INSERT INTO tipos_ativos (descricao) VALUES (%s)",
            (descricao,)
        )
        conn.commit()
        return redirect("/tipos")

    # ---------- FILTRO (GET) ----------
    descricao_filtro = request.args.get("descricao", "").strip()

    where = ""
    params = []

    if descricao_filtro:
        where = "WHERE LOWER(descricao) LIKE LOWER(%s)"
        params.append(f"%{descricao_filtro}%")

    cur.execute(f"""
        SELECT id, descricao
        FROM tipos_ativos
        {where}
        ORDER BY id DESC
    """, params)

    tipos = cur.fetchall()

    cur.close()
    conn.close()

    filtros = {"descricao": descricao_filtro}

    return render_template("tipos_ativos.html", tipos=tipos, filtros=filtros)


@app.route("/tipos/edit", methods=["POST"])
def editar_tipo():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tipos_ativos
        SET descricao = %s
        WHERE id = %s
    """, (request.form["descricao"], request.form["id"]))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/tipos")


@app.route("/tipos/delete", methods=["POST"])
def excluir_tipo():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM tipos_ativos WHERE id=%s", (request.form["id"],))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/tipos")

# ==================================================
# ATIVOS (COM FILTRO + NOVO + EDITAR/EXCLUIR)
# ==================================================
@app.route("/ativos", methods=["GET", "POST"])
def ativos():
    conn = get_connection()
    cur = conn.cursor()

    # lista de tipos (para filtro / novo / editar)
    cur.execute("SELECT id, descricao FROM tipos_ativos ORDER BY descricao")
    tipos = cur.fetchall()

    # ---------- POST = NOVO ----------
    if request.method == "POST":
        ticker = request.form["ticker"].strip().upper()
        nome = request.form.get("nome", "").strip()
        tipo_id = request.form["tipo_id"]

        cur.execute("""
            INSERT INTO ativos (ticker, nome, tipo_id)
            VALUES (%s, %s, %s)
        """, (ticker, nome, tipo_id))

        conn.commit()
        cur.close()
        conn.close()
        return redirect("/ativos")

    # ---------- FILTROS (GET) ----------
    ticker_filtro = request.args.get("ticker", "").strip()
    nome_filtro = request.args.get("nome", "").strip()
    tipo_id_filtro = request.args.get("tipo_id", "").strip()

    where = []
    params = []

    if ticker_filtro:
        where.append("LOWER(a.ticker) LIKE LOWER(%s)")
        params.append(f"%{ticker_filtro}%")

    if nome_filtro:
        where.append("LOWER(a.nome) LIKE LOWER(%s)")
        params.append(f"%{nome_filtro}%")

    if tipo_id_filtro:
        where.append("a.tipo_id = %s")
        params.append(tipo_id_filtro)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    cur.execute(f"""
        SELECT a.id, a.ticker, a.nome, a.tipo_id, t.descricao
        FROM ativos a
        JOIN tipos_ativos t ON a.tipo_id = t.id
        {where_sql}
        ORDER BY a.id DESC
    """, params)

    ativos = cur.fetchall()

    cur.close()
    conn.close()

    filtros = {
        "ticker": ticker_filtro,
        "nome": nome_filtro,
        "tipo_id": tipo_id_filtro
    }

    return render_template("ativos.html", ativos=ativos, tipos=tipos, filtros=filtros)


@app.route("/ativos/edit", methods=["POST"])
def editar_ativo():
    conn = get_connection()
    cur = conn.cursor()

    ativo_id = request.form["id"]
    ticker = request.form["ticker"].strip().upper()
    nome = request.form.get("nome", "").strip()
    tipo_id = request.form["tipo_id"]

    cur.execute("""
        UPDATE ativos
        SET ticker = %s,
            nome = %s,
            tipo_id = %s
        WHERE id = %s
    """, (ticker, nome, tipo_id, ativo_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/ativos")


@app.route("/ativos/delete", methods=["POST"])
def excluir_ativo():
    conn = get_connection()
    cur = conn.cursor()

    ativo_id = request.form["id"]

    # Se existir FK (aportes/dividendos) pode dar erro ao excluir.
    # Depois podemos melhorar com "soft delete" ou mensagem mais amigável.
    cur.execute("DELETE FROM ativos WHERE id = %s", (ativo_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/ativos")

# ==================================================
# APORTES (COM FILTRO + NOVO + EDITAR/EXCLUIR)
# ==================================================
@app.route("/aportes", methods=["GET", "POST"])
def aportes():
    conn = get_connection()
    cur = conn.cursor()

    # ---------- POST = CRIAR NOVO APORTE ----------
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
        return redirect("/aportes")

    # ---------- GET = LISTAR COM FILTROS ----------
    # filtros via querystring: /aportes?ativo_id=1&data_aporte=2026-02-06&quantidade=10&valor_unitario=9.90
    ativo_id = request.args.get("ativo_id", "").strip()
    data_aporte = request.args.get("data_aporte", "").strip()
    quantidade = request.args.get("quantidade", "").strip()
    valor_unitario = request.args.get("valor_unitario", "").strip()

    where = []
    params = []

    if ativo_id:
        where.append("ap.ativo_id = %s")
        params.append(ativo_id)

    if data_aporte:
        where.append("ap.data_aporte = %s")
        params.append(data_aporte)

    if quantidade:
        where.append("ap.quantidade = %s")
        params.append(quantidade)

    if valor_unitario:
        where.append("ap.valor_unitario = %s")
        params.append(valor_unitario)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    # dropdown de ativos (para filtro e novo)
    cur.execute("SELECT id, ticker FROM ativos ORDER BY ticker")
    ativos = cur.fetchall()

    # lista de aportes (agora trazendo o ID do aporte)
    cur.execute(f"""
        SELECT ap.id, a.ticker, ap.data_aporte, ap.quantidade, ap.valor_unitario, ap.ativo_id
        FROM aportes ap
        JOIN ativos a ON ap.ativo_id = a.id
        {where_sql}
        ORDER BY ap.id DESC
    """, params)
    aportes = cur.fetchall()

    cur.close()
    conn.close()

    # repassa os filtros para manter preenchido no HTML
    filtros = {
        "ativo_id": ativo_id,
        "data_aporte": data_aporte,
        "quantidade": quantidade,
        "valor_unitario": valor_unitario
    }

    return render_template("aportes.html", aportes=aportes, ativos=ativos, filtros=filtros)


@app.route("/aportes/edit", methods=["POST"])
def editar_aporte():
    conn = get_connection()
    cur = conn.cursor()

    aporte_id = request.form["id"]
    ativo_id = request.form["ativo_id"]
    data_aporte = request.form["data_aporte"]
    quantidade = request.form["quantidade"]
    valor_unitario = request.form["valor_unitario"]

    cur.execute("""
        UPDATE aportes
        SET ativo_id=%s, data_aporte=%s, quantidade=%s, valor_unitario=%s
        WHERE id=%s
    """, (ativo_id, data_aporte, quantidade, valor_unitario, aporte_id))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/aportes")


@app.route("/aportes/delete", methods=["POST"])
def excluir_aporte():
    conn = get_connection()
    cur = conn.cursor()

    aporte_id = request.form["id"]
    cur.execute("DELETE FROM aportes WHERE id=%s", (aporte_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/aportes")


# ==================================================
# DIVIDENDOS (COM FILTRO + NOVO + EDITAR/EXCLUIR)
# ==================================================
@app.route("/dividendos", methods=["GET", "POST"])
def dividendos():
    conn = get_connection()
    cur = conn.cursor()

    # dropdown de ativos (para filtro/novo/editar)
    cur.execute("SELECT id, ticker FROM ativos ORDER BY ticker")
    ativos = cur.fetchall()

    # ---------- POST = NOVO ----------
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
        cur.close()
        conn.close()
        return redirect("/dividendos")

    # ---------- FILTROS (GET) ----------
    ativo_id = request.args.get("ativo_id", "").strip()
    data_pagamento = request.args.get("data_pagamento", "").strip()
    valor_recebido = request.args.get("valor_recebido", "").strip()

    where = []
    params = []

    if ativo_id:
        where.append("d.ativo_id = %s")
        params.append(ativo_id)

    if data_pagamento:
        where.append("d.data_pagamento = %s")
        params.append(data_pagamento)

    if valor_recebido:
        where.append("d.valor_recebido = %s")
        params.append(valor_recebido)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    # lista (traz ID + ativo_id para editar)
    cur.execute(f"""
        SELECT d.id, a.ticker, d.data_pagamento, d.valor_recebido, d.ativo_id
        FROM dividendos d
        JOIN ativos a ON d.ativo_id = a.id
        {where_sql}
        ORDER BY d.id DESC
    """, params)

    dividendos_lista = cur.fetchall()

    cur.close()
    conn.close()

    filtros = {
        "ativo_id": ativo_id,
        "data_pagamento": data_pagamento,
        "valor_recebido": valor_recebido
    }

    return render_template("dividendos.html",
                           dividendos=dividendos_lista,
                           ativos=ativos,
                           filtros=filtros)


@app.route("/dividendos/edit", methods=["POST"])
def editar_dividendo():
    conn = get_connection()
    cur = conn.cursor()

    dividendo_id = request.form["id"]

    cur.execute("""
        UPDATE dividendos
        SET ativo_id = %s,
            data_pagamento = %s,
            valor_recebido = %s
        WHERE id = %s
    """, (
        request.form["ativo_id"],
        request.form["data_pagamento"],
        request.form["valor_recebido"],
        dividendo_id
    ))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dividendos")


@app.route("/dividendos/delete", methods=["POST"])
def excluir_dividendo():
    conn = get_connection()
    cur = conn.cursor()

    dividendo_id = request.form["id"]
    cur.execute("DELETE FROM dividendos WHERE id = %s", (dividendo_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dividendos")

# ==================================================
# CATEGORIAS FINANCEIRAS (COM FILTRO + NOVO + EDITAR/EXCLUIR)
# ==================================================
@app.route("/categorias", methods=["GET", "POST"])
def categorias():
    conn = get_connection()
    cur = conn.cursor()

    # ---------- POST = NOVO ----------
    if request.method == "POST":
        descricao = request.form["descricao"].strip()
        tipo = request.form["tipo"].strip().upper()

        cur.execute("""
            INSERT INTO categorias_financeiras (descricao, tipo)
            VALUES (%s, %s)
        """, (descricao, tipo))

        conn.commit()
        cur.close()
        conn.close()
        return redirect("/categorias")

    # ---------- FILTROS (GET) ----------
    descricao_filtro = request.args.get("descricao", "").strip()
    tipo_filtro = request.args.get("tipo", "").strip().upper()

    where = []
    params = []

    if descricao_filtro:
        where.append("LOWER(descricao) LIKE LOWER(%s)")
        params.append(f"%{descricao_filtro}%")

    if tipo_filtro:
        where.append("tipo = %s")
        params.append(tipo_filtro)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    cur.execute(f"""
        SELECT id, descricao, tipo
        FROM categorias_financeiras
        {where_sql}
        ORDER BY id DESC
    """, params)

    categorias = cur.fetchall()

    cur.close()
    conn.close()

    filtros = {"descricao": descricao_filtro, "tipo": tipo_filtro}

    return render_template("categorias.html", categorias=categorias, filtros=filtros)


@app.route("/categorias/edit", methods=["POST"])
def editar_categoria():
    conn = get_connection()
    cur = conn.cursor()

    categoria_id = request.form["id"]
    descricao = request.form["descricao"].strip()
    tipo = request.form["tipo"].strip().upper()

    cur.execute("""
        UPDATE categorias_financeiras
        SET descricao = %s,
            tipo = %s
        WHERE id = %s
    """, (descricao, tipo, categoria_id))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/categorias")


@app.route("/categorias/delete", methods=["POST"])
def excluir_categoria():
    conn = get_connection()
    cur = conn.cursor()

    categoria_id = request.form["id"]

    # Atenção: se a categoria estiver sendo usada em movimentações, pode dar erro por FK.
    cur.execute("DELETE FROM categorias_financeiras WHERE id = %s", (categoria_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/categorias")

# ==================================================
# MOVIMENTAÇÕES (COM FILTRO + NOVO + EDITAR/EXCLUIR)
# ==================================================
@app.route("/movimentacoes", methods=["GET", "POST"])
def movimentacoes():
    conn = get_connection()
    cur = conn.cursor()

    # categorias para filtro/novo/editar
    cur.execute("SELECT id, descricao, tipo FROM categorias_financeiras ORDER BY descricao")
    categorias = cur.fetchall()

    # ---------- POST = NOVO ----------
    if request.method == "POST":
        cur.execute("""
            INSERT INTO movimentacoes_financeiras
            (data_movimento, categoria_id, valor, descricao)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["data_movimento"],
            request.form["categoria_id"],
            request.form["valor"],
            request.form.get("descricao") or None
        ))
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/movimentacoes")

    # ---------- FILTROS (GET) ----------
    data_movimento = request.args.get("data_movimento", "").strip()
    categoria_id = request.args.get("categoria_id", "").strip()
    tipo = request.args.get("tipo", "").strip().upper()   # RECEITA/DESPESA (vem da categoria)
    valor = request.args.get("valor", "").strip()

    where = []
    params = []

    if data_movimento:
        where.append("m.data_movimento = %s")
        params.append(data_movimento)

    if categoria_id:
        where.append("m.categoria_id = %s")
        params.append(categoria_id)

    if tipo:
        where.append("c.tipo = %s")
        params.append(tipo)

    if valor:
        where.append("m.valor = %s")
        params.append(valor)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    # lista (traz id e categoria_id para editar)
    cur.execute(f"""
        SELECT m.id, m.data_movimento, c.descricao, c.tipo, m.valor, m.descricao, m.categoria_id
        FROM movimentacoes_financeiras m
        JOIN categorias_financeiras c ON m.categoria_id = c.id
        {where_sql}
        ORDER BY m.id DESC
    """, params)

    movimentacoes = cur.fetchall()

    cur.close()
    conn.close()

    filtros = {
        "data_movimento": data_movimento,
        "categoria_id": categoria_id,
        "tipo": tipo,
        "valor": valor
    }

    return render_template("movimentacoes.html",
                           movimentacoes=movimentacoes,
                           categorias=categorias,
                           filtros=filtros)


@app.route("/movimentacoes/edit", methods=["POST"])
def editar_movimentacao():
    conn = get_connection()
    cur = conn.cursor()

    mov_id = request.form["id"]

    cur.execute("""
        UPDATE movimentacoes_financeiras
        SET data_movimento = %s,
            categoria_id = %s,
            valor = %s,
            descricao = %s
        WHERE id = %s
    """, (
        request.form["data_movimento"],
        request.form["categoria_id"],
        request.form["valor"],
        request.form.get("descricao") or None,
        mov_id
    ))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/movimentacoes")


@app.route("/movimentacoes/delete", methods=["POST"])
def excluir_movimentacao():
    conn = get_connection()
    cur = conn.cursor()

    mov_id = request.form["id"]
    cur.execute("DELETE FROM movimentacoes_financeiras WHERE id = %s", (mov_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/movimentacoes")

# ==================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
	