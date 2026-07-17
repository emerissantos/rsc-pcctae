# Atualização 0.7.3 para 0.8.0

1. Faça backup do banco, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Não substitua o `.env`.
4. Recrie o container e execute:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_rsc
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

Esta versão possui migration nova no app `auditoria`.

A execução de `seed_rsc` atualiza os grupos e remove dos perfis administrativos permissões de alteração ou exclusão sobre recursos definidos como somente leitura.
