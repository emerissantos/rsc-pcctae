# Padrão visual das telas de requerimento

As capturas em `docs/referencias-ui/` são referências de experiência e organização visual para as futuras telas de requerimento do Sistema RSC-PCCTAE. A implementação deverá usar a identidade institucional da UFSB e componentes próprios; a referência não deverá ser copiada literalmente.

## Estrutura principal

- cabeçalho institucional enxuto;
- conteúdo central com largura máxima e espaços generosos;
- fluxo passo a passo claramente identificado;
- área principal e resumo lateral em telas grandes;
- resumo reposicionado abaixo do conteúdo em telas menores;
- barra de navegação entre etapas fixa na parte inferior quando isso não prejudicar a acessibilidade;
- ações principais sempre visíveis e com hierarquia clara.

## Fluxo sugerido

1. vínculo e dados funcionais;
2. nível pretendido e informações do requerimento;
3. itens do memorial e comprovantes;
4. revisão, declarações e submissão.

O número final de etapas poderá mudar conforme a implementação, mas o usuário deverá visualizar progresso, pendências e etapa atual.

## Componentes reutilizáveis

### Indicador de etapas

- etapa atual destacada em azul;
- etapas concluídas com confirmação visual;
- etapas pendentes neutras;
- etapas com erro ou documento ausente sinalizadas sem depender apenas de cor.

### Resumo lateral fixo

Deverá apresentar, conforme a etapa:

- número do requerimento;
- vínculo selecionado;
- nível pretendido;
- pontuação solicitada;
- quantidade de itens;
- quantidade de documentos;
- pendências impeditivas e alertas;
- progresso para os níveis de RSC.

O resumo será informativo. Todos os valores deverão ser recalculados e validados no backend.

### Grupos e critérios

- grupos apresentados em acordeões;
- critérios com código, descrição e regra de pontuação;
- ação “Adicionar” ou “Preencher” junto ao critério;
- estado visual: não utilizado, em preenchimento, completo, documento pendente ou limite atingido;
- edição de item sem perder o contexto da lista;
- busca textual por critério.

### Item preenchido

Cada item deverá apresentar um resumo com:

- quantidade ou período;
- pontuação calculada e solicitada;
- documentos vinculados;
- ações de editar e remover enquanto o requerimento estiver em rascunho;
- mensagens de validação próximas ao item.

### Cartões de níveis

Os cartões dos níveis deverão mostrar:

- pontuação mínima;
- pontuação atual;
- progresso;
- requisitos adicionais;
- situação: atende, pendente ou não atende;
- destaque do nível solicitado.

### Upload de comprovantes

- seleção e arrastar/soltar;
- barra de progresso;
- limite de 50 MB por arquivo;
- formatos admitidos conforme critério;
- tipo documental;
- vínculo com um ou mais itens, quando permitido;
- visualização, substituição apenas em rascunho e remoção controlada;
- validações novamente executadas no backend.

## Dinamismo

A aplicação continuará server-side com Django. O dinamismo poderá ser implementado com JavaScript progressivo e requisições parciais para:

- adicionar e editar itens;
- atualizar o resumo lateral;
- calcular uma prévia de pontuação;
- enviar arquivos com progresso;
- expandir grupos;
- validar pendências;
- manter a posição da página.

A funcionalidade essencial deverá continuar utilizável sem depender de uma SPA completa.

## Diretrizes visuais

- azul-marinho para identidade institucional e cabeçalho;
- azul vivo para etapa e ação principal;
- laranja para alertas e pontos de atenção;
- verde para requisitos atendidos;
- superfícies brancas sobre fundo cinza muito claro;
- bordas suaves e sombras discretas;
- raio de borda consistente;
- tipografia legível e hierarquia forte;
- uso moderado de ícones;
- contraste compatível com acessibilidade.

## Responsividade e acessibilidade

- navegação completa por teclado;
- foco visível;
- labels associados aos campos;
- mensagens que não dependam somente de cor;
- resumo lateral sem cobrir o conteúdo;
- barra fixa inferior sem ocultar campos;
- acordeões com atributos ARIA;
- anúncios adequados de erros e atualizações dinâmicas;
- suporte a zoom de navegador e telas estreitas.

## Referências armazenadas

- `referencias-ui/requerimento-etapa-dados.png`;
- `referencias-ui/requerimento-itens-resumo-lateral.png`;
- `referencias-ui/requerimento-itens-preenchidos.png`;
- `referencias-ui/requerimento-resumo-exportacao.png`.
