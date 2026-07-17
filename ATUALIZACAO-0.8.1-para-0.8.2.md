# Atualização RSC-PCCTAE 0.8.1 → 0.8.2

## Alterações

- impede o requerente de atuar na triagem do próprio requerimento;
- exclui o processo próprio da fila operacional;
- bloqueia início, visualização operacional, salvamento e conclusão por URL direta;
- aplica a vedação inclusive a membro ativo, operador, staff e superusuário;
- cria regra transversal reutilizável pelo futuro módulo de avaliação.

## Aplicação

1. Faça backup do projeto, banco de dados, `media` e `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Recrie o container web e atualize os arquivos estáticos:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

Não há migration nova nesta versão.
