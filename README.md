# Material de Construção Batatã

Sistema interno de controle de **estoque**, **vendas**, **movimentações** e **orçamentos** para loja de materiais de construção.

- **Backend:** Django + Django REST Framework (TokenAuth)
- **Frontend:** Vue 3 + Vite + TypeScript + Tailwind (com componentes próprios e parte da base ainda usando Vuetify)

## Funcionalidades

- Login obrigatório (token)
- Cadastro de materiais genéricos (cimento, tijolo, areia e outros)
- Cadastro de produtos com marca, unidade de estoque, unidade comercial, custo, preço e ativo/inativo
- Entradas de estoque com atualização de custo médio
- Vendas com baixa automática de estoque e cálculo de lucro
- Cancelamento seguro (DELETE) de entradas e vendas com estorno de estoque
- Exclusão segura de materiais: apaga da base só quando não existe histórico; caso contrário, inativa o cadastro
- Conversões entre unidades de estoque e venda (ex.: `metro`, `lata`, `carrada`, `milheiro`)
- Preços de venda por unidade
- Dashboard e relatórios (resumo, por cliente, por marca)
- Orçamentos com geração de PDF
- Tela de login personalizada com identidade visual da loja
- Modo desktop Windows/offline com Electron + Waitress

## Regras de negócio (resumo)

- **Entrada:** registra quantidade e custo na unidade informada, convertendo para a unidade de estoque quando necessário.
- **Estoque:** mantém `quantidade_atual` e `custo_medio_unitario` (média ponderada).
- **Venda:** usa o custo do estoque para custo/lucro e aceita venda em unidade diferente da unidade de estoque:
	- `custo_unitario` = `Estoque.custo_medio_unitario` (se > 0), senão `Produto.custo_unitario_fabrica`.
	- `lucro_unitario` = `preco_unitario_venda - custo_unitario`.
- **Conversões:** o sistema resolve conversões entre unidades cadastradas no produto.
- **Preço de venda:** pode existir preço específico por unidade; se não existir, o sistema tenta derivar pelo fator de conversão.
- **Cancelamento:** entradas/vendas são marcadas como `cancelada=True` e o estoque é estornado.
- **Exclusão de produto com histórico:** produtos já usados em entradas, vendas, movimentações ou orçamentos não são removidos fisicamente; são inativados para preservar o histórico.

## Atualizações importantes recentes

- **Materiais genéricos:** o sistema deixou de ser apenas “estoque de cimento” e passou a atender diferentes tipos de materiais.
- **Unidades e conversões:** suporte a `KG`, `UNIDADE`, `LATA`, `MILHEIRO`, `CARRADA`, `METRO`, `METRO_QUADRADO`, `METRO_CUBICO` e `PACOTE`.
- **Areia e tijolo:** agora é possível trabalhar corretamente com areia por `metro`, `lata` e `carrada`, além de tijolo por `unidade` e `milheiro`.
- **Formatação de quantidade:** quantidades inteiras passaram a ser exibidas sem zeros desnecessários, por exemplo `2` em vez de `2.0000`.
- **PDF de orçamento:** recebeu layout mais elegante, tabela com linhas suaves, resumo visual melhor e identidade da loja com logo, nome, WhatsApp e endereço.
- **Exclusão com confirmação customizada:** os `confirm()` nativos do navegador foram substituídos por modais próprios nas telas principais.
- **Login com branding:** a tela de login agora usa a logo da loja e paleta visual personalizada.
- **Desktop/offline:** já existe scaffold para empacotar o sistema como app Windows com backend local.
- **Ambiente Python:** atenção para a existência de `venv/` e `.venv/`; dependendo de como o servidor estiver rodando, as dependências precisam estar instaladas no ambiente correto.

## Estrutura do repo

```
manage.py
backend/            # Django settings/urls
cimento/            # App principal (models/services/serializers/views)
frontend/           # Vue 3 + Tailwind + componentes próprios de UI
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

**Observação sobre ambiente:** em algumas máquinas podem coexistir `venv/` e `.venv/`. Verifique qual ambiente está sendo usado pelo Django antes de instalar dependências como `reportlab`, `pillow` ou `waitress`.

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
- `GET/POST/DELETE /api/orcamentos/`
- `GET /api/orcamentos/<id>/pdf/`

Dashboard e relatórios:

- `GET /api/dashboard/`
- `GET /api/relatorios/resumo/`
- `GET /api/relatorios/por-cliente/`
- `GET /api/relatorios/por-marca/`

## Observações

- Banco default é **SQLite** (`db.sqlite3`) para facilitar o dev.
- O frontend exibe loaders/spinners nas listas e mantém um tempo mínimo de 2s nas ações de salvar/excluir para feedback visual.
- A listagem de materiais, entradas, vendas, movimentações e orçamentos usa componentes próprios de UI para manter a identidade visual consistente.
- A exclusão de entradas e vendas é lógica/cancelamento, com estorno de estoque.
- A exclusão de produto é física apenas quando não existe histórico relacionado.

## Identidade visual da loja

- **Nome exibido no sistema:** `Material de Construção Batatã`
- **Logo usada no frontend e no PDF:** `frontend/public/batatalogo.jpeg`
- **Dados usados no PDF de orçamento:**
	- `Telefone WhatsApp: 98 988495700`
	- `Endereço: Avenida Engenheiro Emiliano Macieira 22`
	- `Km 03 BR 135 Tibiri`
	- `São Luís, MA 65095600`

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
