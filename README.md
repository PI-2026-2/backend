# Configuração

Copie `.env.example` para `.env` e troque a senha do banco e `SECRET_KEY`.
O endereço `pi6-db` em `DATABASE_URL` é o nome do serviço dentro do Docker Compose.

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

## API de autenticação

- `POST /cadastro`: recebe `nome`, `email`, `senha`, `telefone`, `data_nascimento` (`AAAA-MM-DD`), `genero` e `tipo` (`TERAPEUTA` ou `PACIENTE`). Retorna `cadastro` com ID e dados públicos. E-mail duplicado retorna 409.
- `POST /login`: recebe `email` e `senha`. Retorna `token` e `usuario` (`id`, `email`, `nome_completo`, `tipo_usuario`). Credenciais inválidas retornam 401.

As rotas de prontuário, mensagens e jogo ainda não existem neste backend.
