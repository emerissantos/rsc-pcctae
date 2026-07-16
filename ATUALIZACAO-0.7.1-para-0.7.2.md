# Atualização RSC-PCCTAE 0.7.1 → 0.7.2

1. Faça backup do banco, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Recrie o container e atualize os arquivos estáticos:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

Não há migration nova nesta versão.

## Alterações visíveis

- resumo das correções solicitadas no topo do requerimento;
- histórico de rodadas de triagem e movimentações do processo;
- responsável, datas, orientação, prazo e observações por item;
- histórico disponível também para a comissão;
- rascunhos de triagem em andamento permanecem privados do requerente.
