# Atualização RSC-PCCTAE 0.8.2 → 0.8.3

1. Faça backup do banco, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Recrie o serviço web e execute:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

Esta versão possui migration para incluir o tipo de auditoria
`DADOS_FUNCIONAIS_VISUALIZADOS`.

Principais mudanças:

- página somente leitura **Meus dados funcionais**;
- nome e e-mail da área do usuário passam a ser clicáveis;
- identificação, servidor e múltiplos vínculos funcionais;
- orientação para procurar o setor de cadastro funcional da Progepe em caso de divergência;
- auditoria da consulta dos dados funcionais.
