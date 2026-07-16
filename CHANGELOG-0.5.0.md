# RSC-PCCTAE 0.5.0

## Triagem documental

- fila própria para a comissão;
- checklist configurável com seis itens iniciais na seed;
- snapshots do checklist por rodada;
- início e conclusão de triagem com histórico;
- encaminhamento para análise quando tudo está conforme;
- devolução para correção quando houver pendência;
- orientação consolidada obrigatória;
- prazo configurável de 10, 30 ou 90 dias;
- ausência de ação automática após o vencimento;
- nova submissão pelo servidor com nova rodada de triagem.

## Segurança e autorização

- acesso limitado a administradores e membros com comissão e mandato vigentes;
- autorização de documentos também passou a considerar as vigências;
- requerente continua sem permissão para alterar dados durante a triagem.

## Banco de dados

- nova migration `apps/triagem/migrations/0001_initial.py`;
- execute `python manage.py migrate` antes de usar a funcionalidade.
