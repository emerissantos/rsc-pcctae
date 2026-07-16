# Atualização RSC-PCCTAE 0.7.0 → 0.7.1

1. Faça backup do banco, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Recrie o container e aplique a migration de permissões:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_rsc
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

## Alteração de perfis

O comando `seed_rsc` cria ou atualiza o perfil **Operação de Triagem**.

O perfil **Gestão de Triagem** permanece responsável somente pelos cadastros estruturais. Usuários administrativos que também precisem atuar nos processos devem receber explicitamente o perfil **Operação de Triagem**.

Contas apenas com `is_staff=True` deixam de acessar a triagem.
