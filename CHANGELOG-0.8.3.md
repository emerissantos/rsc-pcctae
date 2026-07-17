# RSC-PCCTAE 0.8.3

## Meus dados funcionais

Esta versão cria uma página de conferência dos dados institucionais do servidor.

### Acesso

- o nome e o e-mail exibidos no rodapé da barra lateral passam a funcionar como link;
- o nome do servidor na saudação da página inicial também direciona para a página;
- a página não adiciona um novo item ao menu lateral.

### Informações apresentadas

- identidade institucional, login e e-mail;
- situação da conta na origem e datas de sincronização;
- cadastro consolidado do servidor;
- todos os vínculos funcionais associados;
- SIAPE, cargo, lotação, unidade de exercício, regime de trabalho e admissão;
- situação ativa ou inativa de cada vínculo;
- referências técnicas recolhíveis para facilitar o atendimento administrativo.

### Regra de origem dos dados

A tela é somente leitura. Em caso de divergência, o servidor é orientado a procurar o
setor responsável pelo cadastro funcional da Pró-Reitoria de Gestão para Pessoas — Progepe.
Após a correção no sistema de origem, os dados poderão ser atualizados por sincronização
institucional.

### Segurança e auditoria

- a consulta usa exclusivamente o usuário autenticado;
- não existe parâmetro para consultar os dados de outra pessoa;
- a visualização é registrada como `DADOS_FUNCIONAIS_VISUALIZADOS`;
- são auditados ator, usuário afetado, IP, navegador, request ID e quantidade de vínculos.
