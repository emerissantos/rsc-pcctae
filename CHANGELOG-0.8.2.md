# RSC-PCCTAE 0.8.2

## Impedimento de atuação no próprio requerimento

Esta versão aplica segregação de funções às etapas operacionais do processo.

### Regra

O requerente nunca pode realizar triagem, avaliação, relatoria ou deliberação do
próprio requerimento, ainda que também seja membro da comissão, operador autorizado,
staff ou superusuário.

### Triagem

- o requerimento do próprio usuário não aparece na fila;
- início por URL direta retorna HTTP 403;
- acesso a rodada já iniciada retorna HTTP 403;
- salvamento e conclusão retornam HTTP 403;
- o bloqueio não interfere na consulta e correção realizadas como requerente;
- tentativas bloqueadas permanecem registradas pela auditoria transversal.

### Arquitetura

Foi criada a regra compartilhada `pode_atuar_operacionalmente`, que deverá ser
reutilizada pelos futuros módulos de avaliação, relatoria e deliberação.
