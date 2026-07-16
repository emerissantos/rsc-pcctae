# Instalação limpa — RSC-PCCTAE 0.4.2

## 1. Remover o ambiente anterior

Execute dentro da pasta do projeto antigo, antes de excluí-la:

```bash
docker compose down -v --remove-orphans
```

Esse comando remove os containers e os volumes do banco, Redis, mídia e arquivos estáticos daquele projeto.

Depois, remova a pasta antiga e extraia o novo pacote.

## 2. Preparar o novo projeto

```bash
unzip rsc-pcctae-v0.4.2.zip
cd rsc-pcctae-v0.4.2/rsc-pcctae
cp .env.example .env
```

Edite o `.env` e recoloque as credenciais já validadas no ambiente anterior:

- OAuth de login (`UFSB_AUTH_*`);
- cliente técnico (`UFSB_API_*`);
- `x-api-key`;
- senha do PostgreSQL;
- chave secreta do Django.

Não misture endpoints de homologação e produção.

## 3. Subir do zero

```bash
docker compose up -d --build
```

A inicialização executará automaticamente:

```text
migrate
seed_rsc
collectstatic
```

## 4. Conferir

```bash
docker compose ps
docker compose logs -f web
```

Acesse:

```text
http://127.0.0.1:8000/
```

## 5. Primeiro acesso administrativo

Faça login pelo SIGAuth. Depois habilite o usuário como administrador:

```bash
docker compose exec web python manage.py shell -c "
from apps.contas.models import Usuario
u = Usuario.objects.get(username='SEU_LOGIN')
u.is_staff = True
u.is_superuser = True
u.save(update_fields=['is_staff', 'is_superuser'])
print(u.username)
"
```

Painel:

```text
http://127.0.0.1:8000/admin/
```

## 6. Verificação final

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py seed_rsc
docker compose exec web pytest
docker compose exec web ruff check .
```

## 7. Arquivos privados

Em desenvolvimento, os arquivos são entregues pelo Django somente após autenticação. Em produção, `compose.prod.yaml` ativa automaticamente o `X-Accel-Redirect`, e o Nginx lê o volume por uma localização `internal`.

Não crie `location /media/` no proxy e não use `static(settings.MEDIA_URL, ...)` nas URLs do Django. O projeto já está configurado para impedir acesso direto.
