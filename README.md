# Buska Backend

API Flask para gerenciamento de rotas e viagens de transporte escolar.

<<<<<<< HEAD
## Setup Local 
=======
## Setup Local
>>>>>>> 836b9da (docs(readme): update installation and troubleshooting sections)

### Pré-requisitos
- Python 3.12+
- Docker + Docker Compose
- Ansible (para automação)

### Opção 1: Setup Automatizado (Recomendado)

```bash
# Clone o repositório e entre no diretório
git clone https://github.com/BusKa-org/buska-backend.git
cd buska-backend

# Setup completo (venv + dependências + banco + docker)
chmod +x setup.sh start.sh
./start.sh

# Para reinicializar o banco de dados
./start.sh -e clean_database=true
```

A API estará disponível em: **http://localhost:5001/apidocs**

---

### Opção 2: Setup Manual

```bash
# 1. Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependências
make install

# 3. Iniciar banco de dados (em outro terminal)
docker compose -f infra/database.yml up -d

# 4. Popular banco de dados
make initdb

# 5. Rodar servidor
make run
```

A API estará em: **http://localhost:5001** | Swagger: **http://localhost:5001/apidocs**

<<<<<<< HEAD
=======
#### Verificar Instalação

```bash
# Verificar dependências
pip list | grep -E "python-json-logger"

# Verificar security headers
curl -I http://localhost:5001/v1/auth/login | grep -E "X-Content-Type|X-Frame|X-XSS|X-Request-ID"
```

>>>>>>> 836b9da (docs(readme): update installation and troubleshooting sections)
---

## Comandos Disponíveis

### Desenvolvimento Local

```bash
make install       # Instalar dependências
make run          # Rodar servidor (porta 5001)
make initdb       # Criar e popular banco de dados
make deletedb     # Limpar banco de dados
make bdcon        # Conectar ao banco via psql
```

### Docker (Produção)

```bash
make docker-build    # Buildar imagem
make docker-up       # Subir containers (porta 5001)
make docker-down     # Parar containers
make docker-logs     # Ver logs em tempo real
make docker-clean    # Limpar tudo (volumes + imagens)
```

## 📁 Estrutura do Projeto

```
buska-backend/
├── app/                      # Código da aplicação
│   ├── api/
│   │   ├── controllers/      # Lógica dos endpoints
│   │   └── routes/           # Definição das rotas
│   ├── core/
│   │   ├── auth.py          # Autenticação JWT
│   │   └── config.py        # Configurações
│   ├── models/              # Modelos SQLAlchemy
│   └── services/            # Serviços de negócio
├── database/                # Scripts SQL
│   ├── init.sql            # Schema e extensões
│   └── populate.sql        # Dados iniciais
├── docs/                    # Documentação da API
│   └── endpoints/          # Specs YAML (Swagger)
├── infra/
│   ├── database.yml        # Docker Compose (dev)
│   └── terraform/          # Infraestrutura (OpenStack)
├── ansible/                 # Playbooks de automação
│   ├── setup-dev.yml       # Setup local
│   ├── run-docker.yml      # Deploy Docker
│   └── deploy-prod.yml     # Deploy OpenStack
├── tests/                   # Testes automatizados
├── Dockerfile              # Build de produção
├── docker-compose.prod.yml # Orquestração (prod)
├── Makefile               # Automação de comandos
├── setup.sh               # Setup automatizado
├── start.sh              # Setup + Docker
└── pyproject.toml        # Dependências Python
```

## Variáveis de Ambiente

Copie `.env.example` para `.env.prod` e configure:

```bash
# Database
DB_USER=buska_user
DB_PASSWORD=senha_segura_aqui
DB_NAME=buska_db

# API
API_PORT=5001
<<<<<<< HEAD
=======
DEBUG=false
>>>>>>> 836b9da (docs(readme): update installation and troubleshooting sections)
JWT_SECRET_KEY=chave_jwt_longa_e_aleatoria
JWT_EXPIRES_HOURS=2
```

<<<<<<< HEAD
## 📚 Documentação da API

A documentação completa e interativa está disponível em:
=======
## 📚 Documentação

### Documentação da API
A documentação completa e interativa da API está disponível em:
>>>>>>> 836b9da (docs(readme): update installation and troubleshooting sections)
- **Swagger UI**: http://localhost:5001/apidocs
- **ReDoc**: http://localhost:5001/redoc

Principais endpoints:
- `POST /auth/login` - Autenticar
- `POST /auth/register` - Criar conta
- `GET /rotas` - Listar rotas
- `GET /viagens` - Listar viagens
- `GET /me` - Dados do usuário autenticado

<<<<<<< HEAD
=======
## 🔒 Segurança

O backend implementa múltiplas camadas de segurança:

### Autenticação & Autorização
- **JWT** com expiração configurável (padrão: 2 horas)
- **RBAC** (Role-Based Access Control): ALUNO, MOTORISTA, GESTOR
- **Isolamento por Prefeitura** (tenant isolation)

### Proteções Implementadas
- ✅ **Security Headers**: CSP, XSS Protection, HSTS, etc.
- ✅ **Audit Logging**: Registro de todas operações sensíveis
- ✅ **Request ID Tracking**: Rastreamento de requisições

>>>>>>> 836b9da (docs(readme): update installation and troubleshooting sections)
## 🚢 Deployment

### OpenStack (Terraform + Ansible)

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply

# Depois, deploy via Ansible
ansible-playbook ansible/deploy-prod.yml
```

### Docker Local

```bash
./start.sh
```

Containers iniciados:
- `buska_api` - Flask API com Gunicorn (porta 5001)
- `buska_db_prod` - PostgreSQL + PostGIS (porta 5432)
<<<<<<< HEAD
=======

## 🐛 Troubleshooting

### Erro: Import errors para utilitários novos
```bash
# Reinstalar dependências
pip install -e "."
```

### Logs não estão em formato legível
```bash
# Adicionar DEBUG=true no .env
echo "DEBUG=true" >> .env

# Limpar cache e reiniciar
find . -type d -name "__pycache__" -exec rm -r {} +
make run
```

### Type checking errors (mypy)
```bash
# Rodar com configurações menos estritas
mypy app --no-strict-optional --ignore-missing-imports
```
>>>>>>> 836b9da (docs(readme): update installation and troubleshooting sections)
