# Para criar o banco de dados e suas tabelas:

```bash
sudo docker compose build
sudo docker compose run backend uv run create_database.py

```

# Para rodar normalmente:
```bash
sudo docker compose build
sudo docker compose up --watch
```
(o --watch é usado para atualizar o código do container automaticamente)
