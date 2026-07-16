# Atualização RSC-PCCTAE 0.6.0 → 0.7.0

1. Faça backup do banco de dados, do diretório `media` e do `.env`.
2. Extraia o pacote incremental sobre a pasta que contém o `manage.py`.
3. Não substitua o `.env`.
4. Recrie o container e aplique as migrations:

```bash
docker compose up -d --build --force-recreate web
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_rsc
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check
docker compose exec web pytest
```

## Novas permissões

A seed cria ou atualiza:

- `Gestão de Pessoas e Acessos`, com consulta, alteração de perfis e importação do SIG;
- permissão `contas.importar_usuario_sig`;
- permissão `contas.simular_usuario` no perfil de administradores.

A função **Logar como** exige simultaneamente:

- `is_staff=True`;
- permissão `contas.simular_usuario` ou condição de superusuário.

A simulação é exclusivamente de leitura e não permite simular superusuários.
