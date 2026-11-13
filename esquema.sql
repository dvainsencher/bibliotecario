-- Índice da biblioteca. Criado automaticamente pelos scripts na primeira execução.

CREATE TABLE IF NOT EXISTS documentos (
  id               INTEGER PRIMARY KEY,
  sha256           TEXT NOT NULL,
  caminho          TEXT UNIQUE NOT NULL, -- caminho atual
  caminho_origem   TEXT,                 -- onde estava antes
  nome_original    TEXT,
  extensao         TEXT,
  tamanho          INTEGER,
  paginas_total    INTEGER,
  tem_texto        INTEGER DEFAULT 1,    -- 0 para escaneado sem OCR
  tipo             TEXT,                 -- artigo, livro, capitulo, tese, fichamento,
                                         -- politica, noticia, dados, outro
  titulo           TEXT,
  autores          TEXT,                 -- separados por ponto e vírgula
  ano              TEXT,
  fonte            TEXT,                 -- revista, editora, órgão ou veículo
  doi              TEXT,
  idioma           TEXT,
  tags             TEXT,                 -- da lista em tags.md, separadas por ponto e vírgula
  resumo           TEXT,
  nome_sugerido    TEXT,
  sensivel         INTEGER DEFAULT 0,
  situacao         TEXT DEFAULT 'novo',  -- novo, ok, revisar, duplicata, sensivel
  motivo           TEXT,                 -- por que está em revisar, duplicata ou sensivel
  confianca        REAL,
  duplicata_de     INTEGER REFERENCES documentos(id),
  classificado_por TEXT,                 -- modelo usado
  indexado_em      TEXT
);
CREATE INDEX IF NOT EXISTS documentos_sha ON documentos(sha256);

CREATE TABLE IF NOT EXISTS paginas (
  id           INTEGER PRIMARY KEY,
  documento_id INTEGER NOT NULL REFERENCES documentos(id),
  pagina       INTEGER NOT NULL,         -- página do PDF, ou número do bloco
  texto        TEXT,
  UNIQUE (documento_id, pagina)
);

CREATE TABLE IF NOT EXISTS movimentos (
  id           INTEGER PRIMARY KEY,
  documento_id INTEGER REFERENCES documentos(id),
  sha256       TEXT NOT NULL,
  origem       TEXT NOT NULL,
  destino      TEXT NOT NULL,
  operacao     TEXT NOT NULL,            -- copia, move, desfaz
  motivo       TEXT,
  feito_em     TEXT NOT NULL             -- igual para todas as linhas de uma mesma rodada
);

CREATE VIRTUAL TABLE IF NOT EXISTS paginas_fts USING fts5(
  texto, content='paginas', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2'
);

CREATE VIRTUAL TABLE IF NOT EXISTS documentos_fts USING fts5(
  titulo, autores, resumo, tags, content='documentos', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2'
);

-- Gatilhos que mantêm as buscas em dia
CREATE TRIGGER IF NOT EXISTS paginas_ai AFTER INSERT ON paginas BEGIN
  INSERT INTO paginas_fts(rowid, texto) VALUES (new.id, new.texto);
END;
CREATE TRIGGER IF NOT EXISTS paginas_ad AFTER DELETE ON paginas BEGIN
  INSERT INTO paginas_fts(paginas_fts, rowid, texto) VALUES ('delete', old.id, old.texto);
END;
CREATE TRIGGER IF NOT EXISTS paginas_au AFTER UPDATE ON paginas BEGIN
  INSERT INTO paginas_fts(paginas_fts, rowid, texto) VALUES ('delete', old.id, old.texto);
  INSERT INTO paginas_fts(rowid, texto) VALUES (new.id, new.texto);
END;
CREATE TRIGGER IF NOT EXISTS documentos_ai AFTER INSERT ON documentos BEGIN
  INSERT INTO documentos_fts(rowid, titulo, autores, resumo, tags)
  VALUES (new.id, new.titulo, new.autores, new.resumo, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS documentos_ad AFTER DELETE ON documentos BEGIN
  INSERT INTO documentos_fts(documentos_fts, rowid, titulo, autores, resumo, tags)
  VALUES ('delete', old.id, old.titulo, old.autores, old.resumo, old.tags);
END;
CREATE TRIGGER IF NOT EXISTS documentos_au AFTER UPDATE ON documentos BEGIN
  INSERT INTO documentos_fts(documentos_fts, rowid, titulo, autores, resumo, tags)
  VALUES ('delete', old.id, old.titulo, old.autores, old.resumo, old.tags);
  INSERT INTO documentos_fts(rowid, titulo, autores, resumo, tags)
  VALUES (new.id, new.titulo, new.autores, new.resumo, new.tags);
END;
