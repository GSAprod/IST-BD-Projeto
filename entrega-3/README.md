# Entrega 3

A terceira parte do projeto consiste no desenvolvimento de restrições de integridade complexas,
concepção de consultas SQL avançadas, criação de um protótipo de aplicação web e concepção de
consultas OLAP.

Para mais detalhes sobre o enunciado do projeto, consule o ficheiro [enunciado.pdf](./enunciado.pdf)

# Como correr o ambiente de trabalho?

## Correr pela primeira vez

Caso ainda não tenha descarregado o repositório, abra um terminal na pasta onde pretende colocar os ficheiros e crie a cópia local com o comando:

```
$ git clone https://github.com/GSAprod/IST-BD-Projeto.git
```

Alternativamente, também pode usar o GitHub Desktop para descarregar o repositório.

Entre dentro da pasta `entrega-3` e crie o ambiente de trabalho no Docker com o comando:

```
$ docker compose up --build
```

**NOTA:** Pode vir a ser necessário parar os outros containers do `db-workspace`.
Utilize o Docker Desktop para parar todos os contentores da área de trabalho.

Após a criação dos containers no Docker, encontre um excerto nos logs que seja semelhante à passagem abaixo:

```
entrega-3-notebook-1  |     Or copy and paste one of these URLs:
entrega-3-notebook-1  |         http://7fd8c38e99bd:8888/lab?token=f83ee982668ebe66bee2dbeb5875d14131a1d118d1e0fa12
entrega-3-notebook-1  |         http://127.0.0.1:8888/lab?token=f83ee982668ebe66bee2dbeb5875d14131a1d118d1e0fa12
```

Copie o último link e cole num browser para aceder ao notebook do Jupyter.

Abra um novo terminal dentro do notebook (com o +) e estabeleça a ligação com o PostgreSQL:

```
$ psql -h postgres -U postgres
```
Pass: `postgres`

Crie um novo utilizador `db` com passe `db` e uma base de dados `db`, tendo como administrador o utilizador `db`:

```sql
CREATE USER db WITH PASSWORD 'db';
CREATE DATABASE db
	WITH
	OWNER = db
	ENCODING = 'UTF8';
GRANT ALL ON DATABASE db TO db;
```

Saia da sessão com `\q` e crie uma nova sessão com o utilizador `db`:
```
$ psql -h postgres -U db
```
Pass: `db`

Para usar a base de dados da 3a entrega, abra o [E3-report.ipynb](./work/E3-report.ipynb) e corra as células de código necessárias para criar as tabelas e inserir os dados de entrada nas mesmas.

## Correr após a primeira vez

Corra o seguinte comando dentro da pasta `entrega-3`:

```
$ docker compose up
```
