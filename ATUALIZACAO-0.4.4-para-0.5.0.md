# Atualização RSC-PCCTAE 0.4.4 → 0.5.0

1. Faça backup do banco, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Não substitua o `.env`.
4. Recrie o container e aplique a migration:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_rsc
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

A seed cria ou atualiza os seis itens iniciais do checklist e a configuração padrão de 30 dias, sem duplicar registros.

## Nova configuração

No painel administrativo, acesse **Triagem → Configurações da triagem** para escolher 10, 30 ou 90 dias. O vencimento não produz ação automática.
