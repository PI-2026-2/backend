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

## API do aplicativo

As rotas abaixo exigem `Authorization: Bearer <access_token>` obtido no login.

- `GET /patients`: lista os pacientes vinculados ao terapeuta ou a ficha do próprio paciente.
- `POST /patients`: cadastra um paciente e cria o vínculo com o terapeuta autenticado. Aceita os campos de `/cadastro`, mais `diagnosis` e `goal`.
- `GET/POST /patients/{patient_id}/notes` e `PUT /patients/{patient_id}/notes/{note_id}`: evoluções clínicas acessíveis apenas ao terapeuta vinculado.
- `GET /conversations`: mensagens de todas as conversas do usuário.
- `GET/POST /messages`: histórico e envio de mensagens. O terapeuta informa `patient_id`; o paciente usa seu vínculo.
- `GET /catalog`: temas, baralhos e cartas ativos persistidos no banco.
- `GET/POST /programs`: jogo de sete cartas de um baralho para um paciente.
- `GET/POST /responses`: respostas da carta do dia ou da sessão.

O cadastro público de paciente pode incluir `terapeuta_email` para criar o vínculo ao entrar. O aplicativo solicita esse campo. Cadastros de pacientes feitos por um terapeuta usam `POST /patients` e já ficam vinculados. Pacientes previamente cadastrados sem vínculo não aparecem na lista de terapeutas; será necessário criar um fluxo próprio de convite/vinculação para essas contas.

Depois de atualizar o código, execute `create_database.py` novamente para criar as tabelas novas (`patient_links`, `clinical_notes`, `chat_entries`, `card_programs` e `card_responses`). O comando cria tabelas ausentes e preserva as existentes.

O catálogo precisa ser importado antes de usar o jogo:

```bash
sudo docker compose run backend uv run importar_cartas.py caminho/para/cartas.csv --usuario-id 1
```

O CSV requer `collection_name`, `deck_name`, `subtheme`, `question` e `active`. O banco atual não possui classificação de carta; a API informa `Sem classificação` até esse campo existir no modelo de dados.
