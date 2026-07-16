# RSC-PCCTAE 0.7.1 — Correção das autorizações da triagem

## Correção principal

O atributo `is_staff` não concede mais acesso automático à fila, aos processos ou às operações de triagem.

A autorização agora é centralizada em `apps/triagem/permissions.py` e considera somente:

- superusuário;
- participação ativa em comissão vigente vinculada ao requerimento;
- permissões operacionais explícitas.

## Permissões operacionais

- `triagem.acessar_fila_triagem`;
- `triagem.iniciar_triagem`;
- `triagem.alterar_triagem`;
- `triagem.concluir_triagem`.

## Perfis

- **Gestão de Triagem**: mantém apenas os cadastros estruturais, como checklist e prazo de correção;
- **Operação de Triagem**: acessa a fila e executa as operações do processo;
- **Administradores do RSC-PCCTAE**: recebe também as permissões operacionais.

Membros ativos de comissão continuam autorizados pela própria participação, sem necessidade de grupo adicional.

## Proteções adicionais

- membro inativo deixa de visualizar o item Triagem no menu;
- staff sem permissão recebe HTTP 403 na fila e em URLs diretas;
- acesso direto ao requerimento e aos comprovantes segue a mesma autorização operacional;
- consulta ampliada não permite editar o preenchimento do requerente;
- permissão de acesso à fila, isoladamente, não autoriza iniciar, alterar ou concluir.
