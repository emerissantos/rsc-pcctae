# Atualização RSC-PCCTAE 0.8.0 → 0.8.1

## Alterações

- geração do formulário F-00 em DOCX editável;
- preenchimento automático com dados funcionais e itens do requerimento;
- relação numerada dos comprovantes por item;
- campos ausentes destacados para complementação manual;
- auditoria da geração do formulário;
- botão de download no detalhe e na revisão do requerimento.

## Aplicação

1. Faça backup do banco, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Recrie o container e aplique a migration:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

A reconstrução da imagem é necessária porque a versão adiciona a dependência `python-docx`.
