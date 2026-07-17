# RSC-PCCTAE 0.7.3 — Isolamento da Central de Cadastros

## Correção de autorização

A Central de Cadastros agora exige um perfil funcional administrativo próprio. Não concedem mais acesso:

- o atributo `is_staff`;
- permissões de modelo atribuídas diretamente ao usuário;
- o perfil **Operação de Triagem**, embora ele possua permissões técnicas de consulta necessárias à fila operacional.

O superusuário permanece como única exceção de acesso emergencial implícito.

## Requerente puro

Uma conta sem perfil funcional administrativo visualiza somente seus próprios requerimentos e os demais recursos comuns do requerente. O menu **Cadastros** não é renderizado e tentativas de URL direta retornam HTTP 403.

Para corrigir uma conta que acumulou acessos antigos:

```bash
docker compose exec web python manage.py configurar_como_requerente LOGIN --confirmar
```

O comando remove grupos funcionais gerenciados, permissões diretas e as flags `is_staff` e `is_superuser`.

## Validação

- nenhuma migration necessária;
- 65 testes aprovados;
- testes específicos para antigo staff, permissão residual e Operação de Triagem;
- Django check, Ruff e compilação Python aprovados.
