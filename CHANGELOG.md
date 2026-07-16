# Changelog

## 0.4.2

- Estrutura física dos comprovantes simplificada para `requerimentos/<numero>/requisito-<codigo>/item-<codigo>/`.
- Número público único do requerimento utilizado como pasta raiz, sem exposição do SIAPE.
- UUID mantido no nome físico para impedir colisões de arquivos.
- Upload de múltiplos comprovantes por item mantido e validado.
- Validação de quantidade inteira confirmada no frontend, backend e model.

## 0.4.1 — upload funcional e documentos privados

- implementado upload real de um ou vários comprovantes por item;
- um único arquivo pode comprovar toda a quantidade declarada, ou vários arquivos podem ser anexados ao mesmo item;
- documentos organizados por SIAPE, data do requerimento, número do pedido, requisito e item;
- nomes físicos recebem UUID para evitar colisões;
- removida qualquer rota pública de `MEDIA_ROOT`, inclusive em desenvolvimento;
- criado endpoint autenticado e autorizado para acesso aos comprovantes;
- em produção, o Django autoriza e o Nginx entrega o arquivo por `X-Accel-Redirect` em localização `internal`;
- storage privado impede a geração de `arquivo.url`;
- links do sistema apontam somente para o endpoint protegido;
- resposta de download usa `no-store`, `nosniff` e `Content-Disposition: attachment`;
- acesso permitido ao requerente, administradores e membros ativos da comissão associada;
- painel administrativo não expõe o caminho público do arquivo;
- quantidade inteira validada no navegador e obrigatoriamente no backend;
- campo inteiro passou a usar entrada textual numérica para evitar frações aceitas por alguns navegadores;
- adicionados testes de múltiplos anexos, estrutura de diretórios, privacidade, autorização e cálculo inteiro.

## 0.4.0 — reconstrução simplificada

- removidos ciclos, normas e versões normativas;
- criado módulo `pontuacao` com níveis, requisitos e itens;
- criado comando `seed_rsc` com 6 requisitos, 57 itens e 6 níveis;
- cálculo reduzido a item × quantidade, com limite opcional;
- condições de titular e substituto convertidas em itens independentes;
- implementados requerimentos, lançamentos, múltiplos anexos, snapshots e submissão;
- implementados cadastros de comissões e membros;
- preservada a integração OAuth2 e APIs UFSB validada anteriormente;
- interface redesenhada com menu lateral, etapas, cards, acordeões e resumo lateral;
- seed automática e idempotente na inicialização do container;
- 23 testes automatizados aprovados.
