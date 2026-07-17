# Atualização 0.7.2 para 0.7.3

## Alterações

- Central de Cadastros restrita a perfis funcionais próprios;
- `is_staff` não concede acesso à Central;
- permissões diretas isoladas não concedem acesso à Central;
- o perfil **Operação de Triagem** permanece na fila operacional, sem visualizar Cadastros;
- novo comando para converter uma conta em requerente puro.

## Aplicação

1. Faça backup do projeto e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Recrie o serviço web:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_rsc
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

Não há migration nova nesta versão.

## Corrigir uma conta que deve ser somente requerente

```bash
docker compose exec web python manage.py configurar_como_requerente LOGIN --confirmar
```

O comando remove os perfis funcionais gerenciados pelo sistema, limpa permissões diretas e define `is_staff=False` e `is_superuser=False`.
