# Atualização RSC-PCCTAE 0.5.0 → 0.6.0

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

Não há migration nova nesta versão. O comando `seed_rsc` passa a criar ou atualizar também os grupos de acesso da Central de Cadastros.

## Após a atualização

1. Entre com um superusuário ou usuário `is_staff`.
2. Acesse **Cadastros → Pessoas e acessos → Usuários**.
3. Edite cada usuário administrativo e atribua os perfis adequados.

A tela **Meus requerimentos** permanece pessoal. Usuários de comissão acessam processos de trabalho pela fila de triagem e, futuramente, pelas filas de avaliação.
