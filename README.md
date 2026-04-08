# Estoque de Cimento

Sistema interno de controle de **estoque** e **vendas** de cimento.

- **Backend:** Django + Django REST Framework (TokenAuth)
- **Frontend:** Vue 3 + Vite + TypeScript + Vuetify + Tailwind

## Funcionalidades

- Login obrigatório (token)
- Cadastro de produtos (marca, peso, custo de fábrica, preço de loja, ativo/inativo)
- Entradas de estoque (custo de compra) com atualização de custo médio
- Vendas com baixa automática de estoque e cálculo de lucro
- Cancelamento seguro (DELETE) de entradas e vendas com estorno de estoque
- Dashboard e relatórios (resumo, por cliente, por marca)

## Regras de negócio (resumo)

- **Entrada:** registra quantidade e **custo unitário de compra** (`custo_unitario_fabrica`).
- **Estoque:** mantém `quantidade_atual` e `custo_medio_unitario` (média ponderada).
- **Venda:** usa o custo do estoque para custo/lucro:
	- `custo_unitario` = `Estoque.custo_medio_unitario` (se > 0), senão `Produto.custo_unitario_fabrica`.
	- `lucro_unitario` = `preco_unitario_venda - custo_unitario`.
- **Cancelamento:** entradas/vendas são marcadas como `cancelada=True` e o estoque é estornado.

## Estrutura do repo

```
manage.py
backend/            # Django settings/urls
cimento/            # App principal (models/services/serializers/views)
frontend/           # Vue 3 + Vuetify + Tailwind
requirements.txt
```

## Requisitos

- Python (3.x)
- Node.js (recomendado LTS) + npm

## Como rodar (Windows + bash.exe)

### 1) Backend (Django)

No root do projeto:

```bash
cd /c/Users/u12512/Projetos/estoque_cimento

# criar/ativar venv (se ainda não existir)
python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt
./venv/Scripts/python.exe manage.py migrate

# (opcional) criar superusuário
./venv/Scripts/python.exe manage.py createsuperuser

./venv/Scripts/python.exe manage.py runserver 8000
```

API base: `http://127.0.0.1:8000/api/`
Admin: `http://127.0.0.1:8000/admin/`

**CORS (dev):** no `backend/settings.py` está liberado para origens locais e em `DEBUG` está com `CORS_ALLOW_ALL_ORIGINS = True`.

### 2) Frontend (Vue/Vite)

Em outro terminal:

```bash
cd /c/Users/u12512/Projetos/estoque_cimento/frontend
npm install
npm run dev
```

Frontend (dev): `http://localhost:3000/`

## Login (usuário demo)

Você pode usar um usuário criado no admin, ou criar um demo via shell:

```bash
cd /c/Users/u12512/Projetos/estoque_cimento
source venv/Scripts/activate
./venv/Scripts/python.exe manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u,created=User.objects.get_or_create(username='demo');\
u.set_password('demo12345'); u.is_active=True; u.save(); print('demo ok')"
```

## Endpoints principais

Autenticação:

- `POST /api/auth/login/` → `{ token, user }`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

Operação:

- `GET/POST/PUT/PATCH/DELETE /api/produtos/`
- `GET /api/estoque/`
- `GET/POST/PATCH/DELETE /api/entradas/` (DELETE = cancelar com estorno)
- `GET/POST/PATCH/DELETE /api/vendas/` (DELETE = cancelar com estorno)
- `GET /api/movimentacoes/`

Dashboard e relatórios:

- `GET /api/dashboard/`
- `GET /api/relatorios/resumo/`
- `GET /api/relatorios/por-cliente/`
- `GET /api/relatorios/por-marca/`

## Observações

- Banco default é **SQLite** (`db.sqlite3`) para facilitar o dev.
- O frontend exibe loaders/spinners nas listas e mantém um tempo mínimo de 2s nas ações de salvar/excluir para feedback visual.

## Rodar como aplicativo Windows (100% offline)

Este projeto já tem um scaffold para rodar como **app instalado** no Windows usando:

- **Django (local)** servido por **Waitress** via `desktop_backend.py`
- **Electron** como shell/instalador (NSIS) em `desktop/`

### 1) Build do Frontend (gerar `frontend/dist`)

```bash
cd /c/Users/u12512/Projetos/estoque_cimento/frontend
npm install
npm run build
```

### 2) Gerar o EXE do Backend (PyInstaller)

O Electron espera encontrar o executável em `dist_backend/estoque-cimento-backend.exe`.

```bash
cd /c/Users/u12512/Projetos/estoque_cimento
source venv/Scripts/activate

pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --clean --onefile \
	--name "estoque-cimento-backend" \
	desktop_backend.py

# Copia o exe para o local esperado pelo Electron
mkdir -p dist_backend
cp dist/estoque-cimento-backend.exe dist_backend/estoque-cimento-backend.exe
```

Notas:
- O banco `db.sqlite3` será criado automaticamente em um diretório do usuário (configurado pelo Electron).
- O backend faz `migrate` automaticamente no startup.

### 3) Gerar o instalador (Electron + NSIS)

```bash
cd /c/Users/u12512/Projetos/estoque_cimento/desktop
npm install
npm run dist
```

Saída: `desktop/dist/` (vai conter o instalador `.exe` do NSIS).

### Como o app funciona

- Ao abrir o aplicativo:
	- o Electron inicia o backend local em `127.0.0.1:8000`
	- espera `GET /api/health/` responder
	- abre a UI em `http://127.0.0.1:8000/` (SPA servida do `frontend/dist`)
