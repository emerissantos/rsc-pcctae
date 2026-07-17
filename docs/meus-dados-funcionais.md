# Meus dados funcionais

A página `/meus-dados/` permite que o usuário autenticado confira as informações
institucionais sincronizadas para o RSC-PCCTAE.

## Origem

Os dados são lidos de `IdentidadeExterna`, `PessoaInstitucional`, `Servidor` e
`VinculoFuncional`. A seleção começa pelas identidades vinculadas ao próprio usuário
autenticado e prioriza a identidade ativa e sincronizada mais recentemente.

## Somente leitura

Nenhum dado funcional pode ser alterado pela página. Havendo divergência, a orientação
é procurar o setor responsável pelo cadastro funcional da Progepe. O sistema deve receber
a correção por uma sincronização posterior da fonte institucional.

## Privacidade

A rota não recebe identificador de usuário. Portanto, não permite escolher ou consultar
outra pessoa. Em uma sessão de simulação, são apresentados os dados do usuário simulado,
mantendo o técnico como ator real na auditoria.

## Auditoria

Cada acesso registra `DADOS_FUNCIONAIS_VISUALIZADOS`, com contexto da requisição e
quantidade de vínculos encontrados, sem copiar integralmente os dados funcionais para o log.
