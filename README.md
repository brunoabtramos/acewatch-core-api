# AceWatch Core API 🎾

API principal do sistema AceWatch desenvolvida com FastAPI e PostgreSQL. Responsável pela autenticação JWT, gerenciamento de dados e comunicação com o frontend.

## 🔧 Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **PostgreSQL** - Banco de dados relacional
- **SQLAlchemy** - ORM para Python
- **Alembic** - Migrations de banco
- **JWT** - Autenticação segura
- **Pydantic** - Validação de dados
- **WebSockets** - Comunicação em tempo real

## 🚀 Instalação Local

### Pré-requisitos

- Python 3.11+
- PostgreSQL 13+
- pip

### 1. Clone e Configure

```bash
git clone <url-do-repositorio>
cd acewatch-core-api

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados

```bash
# Criar banco PostgreSQL
createdb acewatch_db

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações
```

### 3. Executar Aplicação

```bash
# Modo desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ou usar o script
python main.py
```

## 🐳 Docker

### Executar com Docker

```bash
# Construir imagem
cd .
# Executar container
docker run -d \
  --name acewatch-core-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  acewatch-core-api
```

### Health Check

O container possui health check automático verificando o endpoint `/health`

## 📊 API Endpoints

### Autenticação

- `POST /auth/register` - Registro de usuário
- `POST /auth/login` - Login (retorna JWT)
- `GET /auth/me` - Dados do usuário autenticado

### Partidas

- `GET /matches` - Listar partidas com filtros
  - Query params: `date`, `status`, `page`, `limit`
- `GET /matches/{id}` - Detalhes de uma partida
- `POST /matches` - Criar partida (usado pelo scores-service)

### Favoritos

- `GET /favorites` - Listar favoritos do usuário
- `POST /favorites` - Adicionar aos favoritos
- `DELETE /favorites/{id}` - Remover favorito

### Alertas

- `GET /alerts` - Listar alertas do usuário
- `POST /alerts` - Criar novo alerta
- `PUT /alerts/{id}` - Atualizar alerta
- `DELETE /alerts/{id}` - Remover alerta

### WebSocket

- `WS /ws/live` - Conexão para atualizações em tempo real

### Sistema

- `GET /health` - Status da API

## 🗄️ Modelos de Dados

### User

```python
{
    "id": int,
    "email": str,
    "created_at": datetime
}
```

### Match

```python
{
    "id": int,
    "external_event_id": str,
    "league": str,
    "round": str,
    "home_player": str,
    "away_player": str,
    "start_time": datetime,
    "status": str,  # "Scheduled", "In Play", "Finished"
    "score_json": dict,
    "last_fetch_at": datetime
}
```

### Favorite

```python
{
    "id": int,
    "user_id": int,
    "type": str,  # "player" or "match"
    "external_player_id": str,
    "external_event_id": str,
    "match_id": int,
    "created_at": datetime
}
```

### Alert

```python
{
    "id": int,
    "user_id": int,
    "match_id": int,
    "trigger": str,  # "match_started", "tie_break", "third_set", "match_finished"
    "is_active": bool,
    "created_at": datetime
}
```

## 🔐 Autenticação

A API usa JWT (JSON Web Tokens) para autenticação:

1. **Registro/Login**: Cliente envia credenciais
2. **Token JWT**: API retorna token assinado
3. **Autorização**: Cliente inclui token no header `Authorization: Bearer <token>`
4. **Validação**: API valida token em rotas protegidas

### Configuração JWT

```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🔄 WebSocket para Live Updates

O sistema suporta WebSocket para atualizações em tempo real:

```javascript
// Conectar ao WebSocket
const ws = new WebSocket("ws://localhost:8000/ws/live");

// Receber atualizações
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Atualizar UI com novos dados
};
```

## 📁 Estrutura de Arquivos

```
acewatch-core-api/
├── app/
│   ├── __init__.py
│   ├── auth.py          # Autenticação JWT
│   ├── crud.py          # Operações CRUD
│   ├── database.py      # Configuração do banco
│   ├── models.py        # Modelos SQLAlchemy
│   └── schemas.py       # Schemas Pydantic
├── Dockerfile           # Container Docker
├── main.py             # Aplicação FastAPI
├── requirements.txt    # Dependências Python
├── .env.example       # Exemplo de configuração
└── README.md          # Este arquivo
```

## ⚡ Performance e Otimização

### Índices do Banco

- Índices criados automaticamente via SQL init
- Consultas otimizadas para filtros comuns
- Paginação implementada

### Cache

- SQLAlchemy session pool
- Conexões persistentes
- Queries otimizadas

### Monitoramento

- Health checks automáticos
- Logs estruturados
- Métricas de performance

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio httpx

# Executar testes
pytest

# Com coverage
pytest --cov=app
```

## 📝 Logs

A aplicação gera logs estruturados:

```bash
# Ver logs em desenvolvimento
tail -f app.log

# Ver logs do Docker
docker logs acewatch-core-api -f
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco**

   - Verificar se PostgreSQL está rodando
   - Conferir variáveis de ambiente
   - Testar conexão manual

2. **Token JWT inválido**

   - Verificar SECRET_KEY
   - Confirmar formato do header Authorization
   - Checar expiração do token

3. **Erro de CORS**
   - Verificar configuração CORS no main.py
   - Confirmar origem do frontend

## 🔧 Configuração de Produção

### Variáveis de Ambiente

```env
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=strong-secret-key-for-production
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

### Deploy com Docker

```dockerfile
# Usar imagem de produção
FROM python:3.11-slim

# Configurações de segurança
USER appuser
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health
```

## 📋 TODO / Melhorias Futuras

- [ ] Rate limiting
- [ ] Cache Redis
- [ ] Observabilidade (Prometheus/Grafana)
- [ ] Testes de integração
- [ ] CI/CD pipeline
- [ ] Backup automático do banco

---

Desenvolvido como parte do MVP AceWatch 🎾
