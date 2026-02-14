# Deploy Django + MySQL no Render

## 1) Subir o projeto no GitHub
- Garanta que os arquivos abaixo estao no repositorio:
  - `requirements.txt`
  - `Procfile`
  - `e_commerce/settings.py`
  - `.env.example`

## 2) Criar banco MySQL externo
No Render, para MySQL use servico externo (ex.: Aiven/TiDB/PlanetScale).
Guarde as credenciais:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## 3) Criar Web Service no Render
- New > Web Service > Connect GitHub Repo
- Environment: `Python 3`
- Root Directory: pasta onde esta `manage.py`

## 4) Build e Start Commands
- Build Command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

- Start Command:

```bash
gunicorn e_commerce.wsgi:application
```

## 5) Variaveis de ambiente no Render
Defina em Environment:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<sua-chave-forte>`
- `DJANGO_ALLOWED_HOSTS=<seu-servico>.onrender.com`
- `DJANGO_EXTRA_CORS_ORIGINS=https://sigv.netlify.app`
- `DJANGO_EXTRA_CSRF_TRUSTED_ORIGINS=https://sigv.netlify.app`
- `DJANGO_SECURE_SSL_REDIRECT=true`
- `USE_MYSQL=true`
- `DB_NAME=...`
- `DB_USER=...`
- `DB_PASSWORD=...`
- `DB_HOST=...`
- `DB_PORT=...`

## 6) Teste apos deploy
- Abra `https://<seu-servico>.onrender.com/admin/`
- Teste endpoints `/api/...`
- Teste requests a partir de `https://sigv.netlify.app`

## 7) Problemas comuns
- `400 DisallowedHost`: ajuste `DJANGO_ALLOWED_HOSTS`
- `CORS error`: ajuste `DJANGO_EXTRA_CORS_ORIGINS`
- `CSRF error`: ajuste `DJANGO_EXTRA_CSRF_TRUSTED_ORIGINS`
- `MySQL 2002`: host/porta do banco externo incorretos ou banco offline
