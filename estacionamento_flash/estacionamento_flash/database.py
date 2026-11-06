
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("estacionamento.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    db = get_db()

    db.executescript("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT UNIQUE,
        telefone TEXT,
        email TEXT,
        endereco TEXT,
        criado_em TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT NOT NULL UNIQUE,
        marca TEXT,
        modelo TEXT,
        cor TEXT,
        ano INTEGER,
        tipo TEXT NOT NULL DEFAULT 'Carro',
        tamanho TEXT DEFAULT 'Médio',
        cliente_id INTEGER NOT NULL,
        criado_em TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    );

    CREATE TABLE IF NOT EXISTS vagas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL UNIQUE,
        categoria TEXT NOT NULL DEFAULT 'Normal',
        status TEXT NOT NULL DEFAULT 'Livre'
    );

    CREATE TABLE IF NOT EXISTS precos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modalidade TEXT NOT NULL UNIQUE,
        valor REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        vaga_id INTEGER NOT NULL,
        entrada TEXT NOT NULL,
        saida TEXT,
        valor REAL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Aberta',
        FOREIGN KEY(veiculo_id) REFERENCES veiculos(id),
        FOREIGN KEY(vaga_id) REFERENCES vagas(id)
    );

    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movimentacao_id INTEGER NOT NULL,
        valor REAL NOT NULL,
        forma TEXT NOT NULL,
        data_pagamento TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(movimentacao_id) REFERENCES movimentacoes(id)
    );
    """)

    # Verifica se a coluna criado_em existe na tabela de veículos
    colunas = db.execute(
        "PRAGMA table_info(veiculos)"
    ).fetchall()

    if not any(coluna["name"] == "criado_em" for coluna in colunas):
        db.execute("""
            ALTER TABLE veiculos
            ADD COLUMN criado_em TEXT
        """)

    # Preenche a data dos veículos que já estavam cadastrados
    db.execute("""
        UPDATE veiculos
        SET criado_em = datetime('now','localtime')
        WHERE criado_em IS NULL
    """)

    # Registra automaticamente a data dos novos veículos
    db.executescript("""
    CREATE TRIGGER IF NOT EXISTS preencher_criado_em_veiculo
    AFTER INSERT ON veiculos
    FOR EACH ROW
    WHEN NEW.criado_em IS NULL
    BEGIN
        UPDATE veiculos
        SET criado_em = datetime('now','localtime')
        WHERE id = NEW.id;
    END;
    """)

    # Cria 20 vagas iniciais se ainda não existirem
    if db.execute("SELECT COUNT(*) FROM vagas").fetchone()[0] == 0:
        for i in range(1, 21):
            categoria = (
                "Preferencial" if i in (19, 20)
                else "Moto" if i in (17, 18)
                else "Normal"
            )

            db.execute(
                "INSERT INTO vagas (numero, categoria) VALUES (?, ?)",
                (f"{i:02d}", categoria)
            )

    # Preços iniciais
    defaults = [
        ("Hora", 8.00),
        ("Diária", 45.00),
        ("Mensal", 450.00),
        ("Anual", 4500.00)
    ]

    for modalidade, valor in defaults:
        db.execute("""
            INSERT OR IGNORE INTO precos (modalidade, valor)
            VALUES (?, ?)
        """, (modalidade, valor))

    db.commit()
    db.close()
