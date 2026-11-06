from datetime import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "flash-estacionamento-local"
init_db()

def moeda(valor):
    return ("R$ {:,.2f}".format(float(valor or 0))).replace(",", "X").replace(".", ",").replace("X", ".")
app.jinja_env.filters["moeda"] = moeda

@app.route("/")
def inicio():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM vagas").fetchone()[0]
    livres = db.execute("SELECT COUNT(*) FROM vagas WHERE status='Livre'").fetchone()[0]
    ocupadas = total - livres
    clientes = db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    veiculos = db.execute("SELECT COUNT(*) FROM veiculos").fetchone()[0]
    faturamento = db.execute("""SELECT COALESCE(SUM(valor),0) FROM pagamentos
                                WHERE date(data_pagamento)=date('now','localtime')""").fetchone()[0]
    recentes = db.execute("""SELECT m.id,m.entrada,m.saida,m.status,v.placa,v.modelo,
                                    c.nome cliente,g.numero vaga
                             FROM movimentacoes m
                             JOIN veiculos v ON v.id=m.veiculo_id
                             JOIN clientes c ON c.id=v.cliente_id
                             JOIN vagas g ON g.id=m.vaga_id
                             ORDER BY m.id DESC LIMIT 7""").fetchall()
    db.close()
    return render_template("index.html", total=total, livres=livres, ocupadas=ocupadas,
                           clientes=clientes, veiculos=veiculos, faturamento=faturamento, recentes=recentes)

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    db = get_db()
    if request.method == "POST":
        try:
            db.execute("INSERT INTO clientes(nome,cpf,telefone,email,endereco) VALUES(?,?,?,?,?)",
                       (request.form["nome"].strip(), request.form.get("cpf") or None,
                        request.form.get("telefone"), request.form.get("email"), request.form.get("endereco")))
            db.commit()
            flash("Cliente cadastrado com sucesso.", "success")
        except sqlite3.IntegrityError:
            flash("CPF já cadastrado ou dados inválidos.", "error")
        db.close()
        return redirect(url_for("clientes"))
    lista = db.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    db.close()
    return render_template("clientes.html", clientes=lista)

@app.route("/clientes/excluir/<int:id>", methods=["POST"])
def excluir_cliente(id):
    db = get_db()
    try:
        db.execute("DELETE FROM clientes WHERE id=?", (id,))
        db.commit()
        flash("Cliente excluído.", "success")
    except sqlite3.IntegrityError:
        flash("Este cliente possui veículos vinculados e não pode ser excluído.", "error")
    db.close()
    return redirect(url_for("clientes"))

@app.route("/veiculos", methods=["GET", "POST"])
def veiculos():
    db = get_db()
    if request.method == "POST":
        try:
            db.execute("""INSERT INTO veiculos(placa,marca,modelo,cor,ano,tipo,tamanho,cliente_id)
                          VALUES(?,?,?,?,?,?,?,?)""",
                       (request.form["placa"].upper().replace(" ", ""), request.form.get("marca"),
                        request.form.get("modelo"), request.form.get("cor"), request.form.get("ano") or None,
                        request.form.get("tipo"), request.form.get("tamanho"), request.form["cliente_id"]))
            db.commit()
            flash("Veículo cadastrado com sucesso.", "success")
        except sqlite3.IntegrityError:
            flash("Placa já cadastrada ou cliente inválido.", "error")
        db.close()
        return redirect(url_for("veiculos"))
    lista = db.execute("""SELECT v.*,c.nome cliente FROM veiculos v
                          JOIN clientes c ON c.id=v.cliente_id ORDER BY v.placa""").fetchall()
    pessoas = db.execute("SELECT id,nome FROM clientes ORDER BY nome").fetchall()
    db.close()
    return render_template("veiculos.html", veiculos=lista, clientes=pessoas)

@app.route("/veiculos/excluir/<int:id>", methods=["POST"])
def excluir_veiculo(id):
    db = get_db()
    usado = db.execute("SELECT COUNT(*) FROM movimentacoes WHERE veiculo_id=?", (id,)).fetchone()[0]
    if usado:
        flash("Veículo possui histórico de estacionamento e não pode ser excluído.", "error")
    else:
        db.execute("DELETE FROM veiculos WHERE id=?", (id,))
        db.commit()
        flash("Veículo excluído.", "success")
    db.close()
    return redirect(url_for("veiculos"))

@app.route("/vagas", methods=["GET", "POST"])
def vagas():
    db = get_db()
    if request.method == "POST":
        try:
            db.execute("INSERT INTO vagas(numero,categoria) VALUES(?,?)",
                       (request.form["numero"].strip(), request.form["categoria"]))
            db.commit()
            flash("Vaga adicionada.", "success")
        except sqlite3.IntegrityError:
            flash("Já existe uma vaga com esse número.", "error")
        db.close()
        return redirect(url_for("vagas"))
    lista = db.execute("SELECT * FROM vagas ORDER BY CAST(numero AS INTEGER),numero").fetchall()
    db.close()
    return render_template("vagas.html", vagas=lista)

@app.route("/vagas/excluir/<int:id>", methods=["POST"])
def excluir_vaga(id):
    db = get_db()
    ocupada = db.execute("SELECT status FROM vagas WHERE id=?", (id,)).fetchone()
    if ocupada and ocupada["status"] == "Ocupada":
        flash("Não é possível excluir uma vaga ocupada.", "error")
    else:
        try:
            db.execute("DELETE FROM vagas WHERE id=?", (id,))
            db.commit()
            flash("Vaga excluída.", "success")
        except sqlite3.IntegrityError:
            flash("A vaga possui histórico vinculado e não pode ser excluída.", "error")
    db.close()
    return redirect(url_for("vagas"))

@app.route("/movimentacoes", methods=["GET", "POST"])
def movimentacoes():
    db = get_db()
    if request.method == "POST":
        placa = request.form["placa"].upper().replace(" ", "")
        veiculo = db.execute("SELECT * FROM veiculos WHERE placa=?", (placa,)).fetchone()
        vaga = db.execute("SELECT * FROM vagas WHERE id=? AND status='Livre'", (request.form["vaga_id"],)).fetchone()
        aberta = db.execute("""SELECT COUNT(*) FROM movimentacoes WHERE veiculo_id=? AND status='Aberta'""",
                             (veiculo["id"],)).fetchone()[0] if veiculo else 0
        if not veiculo:
            flash("Placa não encontrada. Cadastre o veículo primeiro.", "error")
        elif not vaga:
            flash("Selecione uma vaga disponível.", "error")
        elif aberta:
            flash("Este veículo já possui uma entrada em aberto.", "error")
        else:
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute("INSERT INTO movimentacoes(veiculo_id,vaga_id,entrada) VALUES(?,?,?)",
                       (veiculo["id"], vaga["id"], agora))
            db.execute("UPDATE vagas SET status='Ocupada' WHERE id=?", (vaga["id"],))
            db.commit()
            flash(f"Entrada registrada para {placa}.", "success")
        db.close()
        return redirect(url_for("movimentacoes"))
    abertas = db.execute("""SELECT m.*,v.placa,v.modelo,c.nome cliente,g.numero vaga
                            FROM movimentacoes m JOIN veiculos v ON v.id=m.veiculo_id
                            JOIN clientes c ON c.id=v.cliente_id JOIN vagas g ON g.id=m.vaga_id
                            WHERE m.status='Aberta' ORDER BY m.id DESC""").fetchall()
    historico = db.execute("""SELECT m.*,v.placa,g.numero vaga FROM movimentacoes m
                              JOIN veiculos v ON v.id=m.veiculo_id JOIN vagas g ON g.id=m.vaga_id
                              ORDER BY m.id DESC LIMIT 20""").fetchall()
    disponiveis = db.execute("SELECT * FROM vagas WHERE status='Livre' ORDER BY numero").fetchall()
    db.close()
    return render_template("movimentacoes.html", abertas=abertas, historico=historico, vagas=disponiveis)

@app.route("/movimentacoes/saida/<int:id>", methods=["POST"])
def registrar_saida(id):
    db = get_db()
    mov = db.execute("""SELECT m.*,v.placa FROM movimentacoes m JOIN veiculos v ON v.id=m.veiculo_id
                        WHERE m.id=? AND m.status='Aberta'""", (id,)).fetchone()
    if not mov:
        flash("Movimentação não encontrada ou já finalizada.", "error")
        db.close()
        return redirect(url_for("movimentacoes"))
    preco = db.execute("SELECT valor FROM precos WHERE modalidade='Hora'").fetchone()
    valor_hora = float(preco["valor"]) if preco else 8.0
    entrada = datetime.strptime(mov["entrada"], "%Y-%m-%d %H:%M:%S")
    minutos = max(1, int((datetime.now() - entrada).total_seconds() / 60))
    horas = max(1, (minutos + 59) // 60)
    valor = round(horas * valor_hora, 2)
    saida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute("UPDATE movimentacoes SET saida=?,valor=?,status='Finalizada' WHERE id=?", (saida, valor, id))
    db.execute("UPDATE vagas SET status='Livre' WHERE id=?", (mov["vaga_id"],))
    db.execute("INSERT INTO pagamentos(movimentacao_id,valor,forma) VALUES(?,?,?)",
               (id, valor, request.form.get("forma", "Dinheiro")))
    db.commit()
    db.close()
    flash(f"Saída de {mov['placa']} registrada. Total: {moeda(valor)} ({horas} hora(s)).", "success")
    return redirect(url_for("movimentacoes"))

@app.route("/precos", methods=["GET", "POST"])
def precos():
    db = get_db()
    if request.method == "POST":
        for modalidade in ("Hora", "Diária", "Mensal", "Anual"):
            try:
                valor = float(request.form.get(modalidade, "0").replace(",", "."))
                if valor >= 0:
                    db.execute("UPDATE precos SET valor=? WHERE modalidade=?", (valor, modalidade))
            except ValueError:
                pass
        db.commit()
        flash("Tabela de preços atualizada.", "success")
        db.close()
        return redirect(url_for("precos"))
    lista = db.execute("SELECT * FROM precos ORDER BY id").fetchall()
    db.close()
    return render_template("precos.html", precos=lista)

@app.route("/relatorios")
def relatorios():
    db = get_db()
    resumo = db.execute("""SELECT COUNT(*) total, COALESCE(SUM(valor),0) receita,
                           COALESCE(AVG(valor),0) ticket FROM pagamentos""").fetchone()
    por_dia = db.execute("""SELECT date(data_pagamento) dia, SUM(valor) total, COUNT(*) qtd
                            FROM pagamentos GROUP BY date(data_pagamento)
                            ORDER BY dia DESC LIMIT 15""").fetchall()
    por_tipo = db.execute("""SELECT g.categoria,COUNT(m.id) quantidade FROM movimentacoes m
                             JOIN vagas g ON g.id=m.vaga_id GROUP BY g.categoria""").fetchall()
    db.close()
    return render_template("relatorios.html", resumo=resumo, por_dia=por_dia, por_tipo=por_tipo)

if __name__ == "__main__":
    app.run(debug=True)
