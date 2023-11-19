# FastAPI Easy Admin

Easy-to-setup FastAPI Admin Panel using SQLAlchemy + AsyncPG


## Requirements

 - Python 3.12+
 - NorthAdmin is based on latest [FastAPI](https://github.com/tiangolo/fastapi) and [SQLAlclhemy](https://github.com/sqlalchemy/sqlalchemy)
 - Any async DB driver like [AsyncPG](https://github.com/MagicStack/asyncpg)
 - Any ASGI Python server like [Uvicorn](https://github.com/encode/uvicorn)

## Example Projects

Let's assume that we have project with:

 - Postgres
 - Some SQLAlchemy models 

In this example we prefer to use AsyncPG as driver.

### Install NorthAdmin

**Poetry**:

```bash
poetry add sqlalchemy asyncpg uvicorn north_admin
```

**PIP**

```bash
pip3 install sqlalchemy asyncpg uvicorn north_admin
pip3 freezee -> requirements.txt
```

### Add NorthAdmin in projects

For example, this is our Posts table:

