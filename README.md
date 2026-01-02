# Buska Backend

API Flask para gerenciamento de rotas e viagens de transporte escolar.

## Setup Local 

### Pré-requisitos
- Python 3.12+
- Docker + Docker Compose
- PostgreSQL client

### Passo a passo rápido

```bash

chmod +x setup.sh
./setup.sh

source .venv/bin/activate
make run
```

A API estará disponível em: **http://localhost:5001/apidocs**

---

## Setup Local - Manual

Se preferir fazer passo a passo:

```bash
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

make initdb
make run
```

A API estará disponível em:
- **http://localhost:5001**
- **http://localhost:5001/apidocs** (Swagger UI)

### Comandos úteis

```bash
make install       # Instalar apenas as dependências
make run          # Rodar servidor de desenvolvimento
make initdb       # Criar/popular banco de dados
make deletedb     # Limpar banco de dados (apaga volumes)
make bdcon        # Conectar ao banco via psql

# Docker (Produção)
make docker-build    # Buildar imagem Docker
make docker-up       # Subir containers em produção
make docker-down     # Parar containers
make docker-logs     # Ver logs em tempo real
make docker-rebuild  # Rebuild completo
make docker-clean    # Limpar tudo (volumes + imagens)
```

## Setup com Docker 

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env.prod

make docker-build
make docker-up

make docker-logs
```

A API estará disponível em: **http://localhost:5001/apidocs**

---

## Automação com Ansible

O Ansible permite automatizar todo o setup com um único comando.

### Setup via Ansible

```bash
./setup.sh

# Reinicializar banco de dados (APAGA dados - use em dev)
./setup.sh -e clean_database=true

# Rodar playbook manualmente
ansible-playbook -i ansible/hosts.ini ansible/setup-dev.yml
# caso queira apagar o banco
ansible-playbook -i ansible/hosts.ini ansible/setup-dev.yml -e clean_database=true
```

---

## Estrutura do Projeto

# 2. Buildar e subir containers
make docker-build
make docker-up

# 3. Verificar logs
make docker-logs
```

A API estará disponível em **http://localhost:5000**

## 📁 Estrutura do Projeto

```
buska-backend/
├── app/                    # Código da aplicação
│   ├── api/               # Controllers e rotas
│   ├── core/              # Configurações
│   ├── models/            # Modelos SQLAlchemy
│   ├── services/          # Lógica de negócio
│   └── utils/             # Utilitários
├── database/              # Scripts SQL
│   ├── init.sql          # Schema inicial
│   └── populate.sql      # Dados de teste
├── infra/                 # Infraestrutura
│   ├── database.yml      # Docker Compose (dev)
│   └── terraform/        # Provisionamento OpenStack
├── ansible/              # Playbooks de automação
├── tests/                 # Testes
├── Dockerfile            # Build de produção
├── docker-compose.prod.yml  # Orquestração produção
├── Makefile              # Automação de comandos
├── setup.sh              # Setup automatizado com Ansible
└── pyproject.toml        # Dependências Python
```

## 🔧 Variáveis de Ambiente

Principais variáveis (`.env.prod`):

```bash
# Database
DB_USER=buska_user
DB_PASSWORD=seu_password_seguro
DB_NAME=buska_db

# API
API_PORT=5000
JWT_SECRET_KEY=chave_jwt_longa_e_aleatoria
JWT_EXPIRES_HOURS=2
```

## 🚢 Deploy no OpenStack

Documentação em desenvolvimento. Infraestrutura gerenciada via Terraform em `infra/terraform/`.

## 📝 API Endpoints

Principais rotas (veja documentação completa em `/apidocs`):

- `POST /auth/login` - Login
- `POST /auth/register` - Registro
- `GET /rotas` - Listar rotas
- `GET /viagens` - Listar viagens
- `GET /me` - Dados do usuário autenticado

## 🧪 Testes

```bash
# Em desenvolvimento
pytest tests/
```

## 📄 Licença

[A definir]
