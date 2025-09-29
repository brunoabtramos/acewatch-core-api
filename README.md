# AceWatch 🎾

**AceWatch** é um sistema completo de monitoramento de tênis em tempo real, desenvolvido seguindo arquitetura de microsserviços. O sistema permite acompanhar partidas ao vivo, criar listas de favoritos e configurar alertas personalizados para eventos específicos das partidas.

## 🏗️ Arquitetura do Sistema

O AceWatch é composto por 3 módulos principais que se comunicam seguindo o padrão REST:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │◄──►│   Core API      │◄──►│ Scores Service  │
│   (React)       │    │   (FastAPI)     │    │   (FastAPI)     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │                 │    │                 │
         └─────────────►│   PostgreSQL    │    │   TheSportsDB   │
                        │   Database      │    │   API (Externa) │
                        │                 │    │                 │
                        └─────────────────┘    └─────────────────┘
```

### Componentes

1. **Frontend (React + Tailwind)**: Interface do usuário com dashboard, favoritos e alertas
2. **Core API (FastAPI + PostgreSQL)**: API principal com autenticação JWT e CRUD completo
3. **Scores Service (FastAPI)**: Serviço de integração com API externa TheSportsDB
4. **PostgreSQL**: Banco de dados para persistência
5. **TheSportsDB API**: Serviço externo para dados de tênis

## 🚀 Tecnologias Utilizadas

### Backend

- **FastAPI** - Framework web moderno para Python
- **PostgreSQL** - Banco de dados relacional
- **SQLAlchemy** - ORM para Python
- **JWT** - Autenticação segura
- **Docker** - Containerização

### Frontend

- **React 18** - Biblioteca JavaScript para UI
- **Vite** - Build tool moderna
- **Tailwind CSS** - Framework CSS utilitário
- **Axios** - Cliente HTTP
- **React Router** - Roteamento
- **Lucide React** - Ícones

### API Externa

- **TheSportsDB** - API gratuita para dados esportivos
  - Licença: Gratuita para uso educacional/desenvolvimento
  - Cadastro: Não necessário (usa chave de teste)
  - Rotas utilizadas: `/eventsday.php`, `/searchplayers.php`

## 📋 Funcionalidades

### ✅ Requisitos Atendidos

- **4 Métodos HTTP**: GET (matches), POST (favorites), PUT (alerts), DELETE (favorites/alerts)
- **Arquitetura de Microsserviços**: 3 módulos independentes
- **API Externa**: Integração com TheSportsDB
- **Banco de Dados**: PostgreSQL com 4 tabelas
- **Dockerfiles**: Cada componente containerizado
- **Autenticação JWT**: Sistema completo de login/registro

### 🎯 Funcionalidades Principais

- 📊 **Dashboard em tempo real** com partidas ao vivo
- ⭐ **Sistema de favoritos** para partidas e jogadores
- 🔔 **Alertas personalizados** para eventos específicos
- 🔐 **Autenticação JWT** segura
- 📱 **Interface responsiva** para todos os dispositivos
- ⚡ **WebSocket** para atualizações em tempo real
- 🎨 **UI moderna** com Tailwind CSS

## 🛠️ Instalação e Configuração

### Pré-requisitos

- Docker 20.0+
- Docker Compose 2.0+
- Node.js 18+ (para desenvolvimento)
- Python 3.11+ (para desenvolvimento)

### 1. Clone os Repositórios

```bash
# Clone o repositório principal
git clone <url-do-repositorio-principal>
cd acewatch

# Os 3 módulos devem estar em repositórios separados:
# - acewatch-core-api
# - acewatch-scores-service
# - acewatch-frontend
```

### 2. Configuração de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite as variáveis de ambiente conforme necessário
nano .env
```

### 3. Executar com Docker Compose

```bash
# Construir e iniciar todos os serviços
docker-compose up --build

# Ou executar em background
docker-compose up -d --build
```

### 4. Verificar os Serviços

Após a inicialização, os serviços estarão disponíveis em:

- **Frontend**: http://localhost:3000
- **Core API**: http://localhost:8000
- **PostgreSQL**: localhost:5435

## 🗂️ Estrutura do Projeto

```
acewatch/
├── acewatch-core-api/          # API principal (FastAPI)
│   ├── app/
│   │   ├── auth.py            # Autenticação JWT
│   │   ├── crud.py            # Operações CRUD
│   │   ├── database.py        # Configuração DB
│   │   ├── models.py          # Modelos SQLAlchemy
│   │   └── schemas.py         # Schemas Pydantic
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── acewatch-scores-service/    # Serviço de scores
│   ├── app/
│   │   ├── data_processor.py  # Processamento de dados
│   │   ├── models.py          # Modelos Pydantic
│   │   └── thesportsdb.py     # Cliente API externa
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── acewatch-frontend/          # Interface React
│   ├── src/
│   │   ├── components/        # Componentes reutilizáveis
│   │   ├── contexts/          # Contextos React
│   │   ├── pages/             # Páginas da aplicação
│   │   └── services/          # Serviços de API
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── database/
│   └── init.sql              # Script de inicialização
├── docker-compose.yml        # Orquestração dos serviços
└── README.md                 # Este arquivo
```

## 🎮 Como Usar

### 1. Acesse a Aplicação

Abra http://localhost:3000 no seu navegador

### 2. Crie uma Conta

- Clique em "Sign up"
- Preencha email e senha
- Faça login automático

### 3. Explore o Dashboard

- Visualize partidas ao vivo com indicador "LIVE"
- Veja partidas agendadas e resultados
- Use filtros por status e data

### 4. Gerencie Favoritos

- Clique no ❤️ em qualquer partida
- Acesse "Favorites" no menu
- Remova favoritos quando desejar

### 5. Configure Alertas

- Clique no 🔔 em qualquer partida
- Escolha o tipo de alerta
- Gerencie em "Alerts"

## 📊 API Endpoints

### Autenticação

- `POST /auth/login` - Login do usuário
- `POST /auth/register` - Registro de usuário
- `GET /auth/me` - Dados do usuário atual

### Partidas

- `GET /matches` - Listar partidas (com filtros)
- `GET /matches/{id}` - Detalhes de uma partida
- `POST /matches` - Criar partida (interno)

### Favoritos

- `GET /favorites` - Listar favoritos do usuário
- `POST /favorites` - Adicionar favorito
- `DELETE /favorites/{id}` - Remover favorito

### Alertas

- `GET /alerts` - Listar alertas do usuário
- `POST /alerts` - Criar alerta
- `PUT /alerts/{id}` - Atualizar alerta
- `DELETE /alerts/{id}` - Remover alerta

## 🔧 Desenvolvimento

### Executar Localmente

#### Core API

```bash
cd acewatch-core-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Scores Service

```bash
cd acewatch-scores-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

#### Frontend

```bash
cd acewatch-frontend
npm install
npm run dev
```

### Executar Testes

```bash
# Testes do backend
docker-compose exec core-api python -m pytest

# Testes do frontend
docker-compose exec frontend npm test
```

## 🌐 API Externa - TheSportsDB

### Informações da API

- **Nome**: TheSportsDB
- **URL**: https://www.thesportsdb.com
- **Licença**: Gratuita para desenvolvimento/educação
- **Cadastro**: Não necessário (chave de teste: "3")
- **Limitações**: Sem livescore real-time na versão gratuita

### Rotas Utilizadas

- `GET /eventsday.php?d=YYYY-MM-DD&s=Tennis` - Eventos por data
- `GET /searchplayers.php?p={query}` - Buscar jogadores
- `GET /lookupevent.php?id={eventId}` - Detalhes do evento

### Tratamento de Dados

Todos os dados da API externa são:

- Processados e normalizados pelo Scores Service
- Armazenados no banco PostgreSQL
- Exibidos através da nossa interface
- **Não redirecionam** para aplicações externas

## 📝 Logs e Monitoramento

### Visualizar Logs

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f core-api
docker-compose logs -f scores-service
docker-compose logs -f frontend
```

### Health Checks

Todos os serviços possuem endpoints de health:

- Core API: `GET /health`
- Scores Service: `GET /health`
- Frontend: `GET /` (nginx)

## 🚨 Troubleshooting

### Problemas Comuns

1. **Porta já em uso**

   ```bash
   # Parar todos os containers
   docker-compose down
   # PostgreSQL configurado para porta 5435 para evitar conflito com instalação local
   # Se ainda houver conflito, modifique as portas no docker-compose.yml
   ```

2. **Banco de dados não conecta**

   ```bash
   # Verificar se o PostgreSQL subiu
   docker-compose logs db
   # Aguardar o health check passar
   ```

3. **Frontend não carrega**
   ```bash
   # Verificar se a API está rodando
   curl http://localhost:8000/health
   # Verificar configuração de proxy no nginx.conf
   ```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é desenvolvido para fins educacionais como parte do MVP do curso de Desenvolvimento Full Stack.

## 👥 Autores

- Desenvolvido como projeto acadêmico
- Utiliza dados da API gratuita TheSportsDB

---

**AceWatch** - Acompanhe o tênis como nunca antes! 🎾✨
