# Sistema RSC-PCCTAE — UFSB

Versão **0.4.0**, reconstruída para instalação limpa.

## Escopo desta versão

O sistema foi simplificado para o fluxo operacional do RSC-PCCTAE:

- autenticação institucional OAuth2/SIGAuth;
- sincronização do usuário, pessoa, servidor e vínculos funcionais pelas APIs da UFSB;
- cadastro de comissões e membros com vigência e histórico;
- requisitos, níveis e itens de pontuação;
- seed idempotente baseada no Decreto nº 13.048/2026;
- requerimentos apresentados a qualquer tempo, sem ciclos;
- preenchimento por **item + quantidade**;
- cálculo automático da pontuação;
- múltiplos anexos por item;
- observação opcional;
- revisão e submissão;
- snapshots da regra usada no lançamento, preservando o histórico;
- interface responsiva inspirada nas capturas de referência fornecidas.

Não há módulo de normas, versões normativas, matrizes ou ciclos de avaliação.

## Regra de cálculo

Cada lançamento usa apenas:

```text
pontuação = quantidade × pontos do item
```

Quando houver limite configurado no item:

```text
pontuação = mínimo(quantidade × pontos do item, limite)
```

Datas, portarias, períodos e demais detalhes não são transcritos para campos estruturados. Eles devem constar no documento comprobatório e serão conferidos pela comissão.

Nos quatro itens do requisito V, as condições de titular e substituto foram transformadas em itens independentes, por exemplo:

- `V.1-T` — CD-02 como titular;
- `V.1-S` — CD-02 como substituto.

## Requisitos técnicos

- Docker 24 ou superior;
- Docker Compose v2;
- acesso aos endpoints de homologação ou produção da UFSB;
- credenciais OAuth de login;
- credenciais técnicas das APIs e `x-api-key`.

## Instalação limpa

### 1. Extraia o projeto

```bash
unzip rsc-pcctae-v0.4.0.zip
cd rsc-pcctae-v0.4.0/rsc-pcctae
```

### 2. Crie o `.env`

```bash
cp .env.example .env
```

Preencha, no mínimo:

```env
DJANGO_SECRET_KEY=uma-chave-segura
POSTGRES_PASSWORD=uma-senha-segura

UFSB_AUTH_CLIENT_ID=
UFSB_AUTH_CLIENT_SECRET=
UFSB_AUTH_USERINFO_API_KEY=

UFSB_API_CLIENT_ID=
UFSB_API_CLIENT_SECRET=
UFSB_API_KEY=
```

Mantenha todos os endpoints no mesmo ambiente: homologação com homologação ou produção com produção.

### 3. Suba os serviços

```bash
docker compose up -d --build
```

Na primeira inicialização, o container executa automaticamente:

```text
python manage.py migrate --noinput
python manage.py seed_rsc
python manage.py collectstatic --noinput
```

A seed é idempotente e pode ser executada em todas as inicializações sem duplicar registros.

### 4. Acompanhe os logs

```bash
docker compose logs -f web
```

### 5. Acesse

```text
http://127.0.0.1:8000/
```

## Tornar o primeiro usuário administrador

Faça o primeiro login pelo SIGAuth. Depois execute, substituindo o login:

```bash
docker compose exec web python manage.py shell -c "
from apps.contas.models import Usuario
u = Usuario.objects.get(username='SEU_LOGIN')
u.is_staff = True
u.is_superuser = True
u.save(update_fields=['is_staff', 'is_superuser'])
print('Administrador habilitado:', u.username)
"
```

O painel administrativo estará disponível em:

```text
http://127.0.0.1:8000/admin/
```

## Comandos úteis

```bash
# Estado dos containers
docker compose ps

# Logs
docker compose logs -f web

# Verificações
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run

# Executar novamente a seed
docker compose exec web python manage.py seed_rsc

# Testes
docker compose exec web pytest

# Lint
docker compose exec web ruff check .

# Shell Django
docker compose exec web python manage.py shell
```

## Reinicialização completa do ambiente

Atenção: este comando remove banco, Redis, arquivos enviados e estáticos persistidos nos volumes do Compose.

```bash
docker compose down -v --remove-orphans
docker compose up -d --build
```

## Estrutura principal

```text
apps/
├── contas/          autenticação e usuário local
├── integracoes/     OAuth2 e APIs institucionais
├── pessoas/         pessoa, servidor e vínculos
├── pontuacao/       níveis, requisitos, itens e seed
├── comissoes/       comissões e membros
├── requerimentos/   pedidos, lançamentos, anexos e histórico
├── auditoria/       base para eventos de auditoria
└── core/            infraestrutura comum e dashboard
```

## Documentação

- `docs/integracao-ufsb.md`
- `docs/modelo-simplificado-rsc.md`
- `docs/padroes-interface-requerimento.md`
- `docs/referencias-ui/`
