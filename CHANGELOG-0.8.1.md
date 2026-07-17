# RSC-PCCTAE 0.8.1

## Formulário F-00 em DOCX editável

- adiciona geração do F-00 diretamente na tela do requerimento;
- gera arquivo `.docx` editável no Word e no LibreOffice;
- preenche nome, SIAPE, cargo, ingresso, lotação, e-mail e nível pretendido;
- calcula pontuação mínima, pontuação apresentada, quantidade de itens e excedente;
- organiza os lançamentos nos critérios I a VI;
- inclui quantidade, unidade, pontos por unidade, pontuação obtida e comprovantes;
- preserva a observação informada pelo requerente em cada item;
- inclui linhas vazias para complementação manual;
- destaca os campos que não existem na base como `[PREENCHER]`;
- registra a geração do documento na auditoria;
- restringe a geração aos usuários autorizados a visualizar o requerimento;
- protege a resposta com cabeçalhos contra cache;
- adiciona `python-docx` às dependências do projeto;
- adiciona migration para o novo tipo de evento de auditoria;
- adiciona testes de conteúdo, autorização e auditoria;
- valida visualmente o DOCX em quatro páginas A4.
