# RSC-PCCTAE 0.7.2 — Histórico de triagem e comunicações

## Experiência do requerente

Quando o processo estiver **Pendente de correção**, o requerimento passa a apresentar um resumo destacado contendo:

- número da rodada;
- data e hora da conclusão;
- responsável que concluiu a triagem;
- prazo para correção;
- orientação consolidada da comissão;
- relação das pendências por item, com as respectivas observações;
- acesso direto à correção do requerimento e ao histórico completo.

## Histórico do processo

Foi criado um componente reutilizável de histórico, exibido no requerimento e na tela operacional da comissão. Ele apresenta:

- todas as rodadas publicadas da triagem;
- responsável inicial e usuário que concluiu cada rodada;
- datas de início e conclusão;
- resultado da rodada;
- prazo registrado como snapshot;
- orientação consolidada;
- checklist completo com situação e observação de cada item;
- movimentações formais de situação do requerimento.

## Privacidade operacional

O requerente visualiza somente rodadas concluídas. Observações salvas enquanto a triagem permanece em andamento são consideradas rascunhos internos da comissão e não são exibidas antes da conclusão.

Membros e operadores autorizados visualizam também a rodada em andamento e conseguem consultar rodadas anteriores na própria tela de triagem.

## Implementação

- criado `apps/requerimentos/history.py` para carregamento padronizado do histórico;
- criado o componente `templates/requerimentos/_historico_processo.html`;
- consultas otimizadas com `select_related` e `Prefetch`;
- nenhuma migration de banco necessária;
- adicionados testes de transparência, privacidade e múltiplas rodadas.
