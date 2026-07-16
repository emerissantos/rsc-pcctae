# Changelog

## 0.7.1 — correção das autorizações da triagem

- remove o acesso implícito à triagem concedido por `is_staff`;
- exige vínculo ativo em comissão vigente, superusuário ou permissões operacionais explícitas;
- separa os perfis Gestão de Triagem e Operação de Triagem;
- restringe início, alteração e conclusão por permissões distintas;
- fecha o acesso direto a requerimentos e comprovantes para staff sem competência operacional;
- adiciona testes de regressão para vínculo inativo, URL direta e permissões parciais.

## 0.7.0 — importação institucional e simulação de usuário

- criada importação administrativa por login, ID do usuário ou ID institucional;
- reutilizado o provisionamento institucional para pessoa, servidor, vínculos, identidade e conta;
- contas importadas permanecem sem senha local e autenticam exclusivamente por OAuth;
- criado perfil Gestão de Pessoas e Acessos;
- adicionadas permissões específicas para importar e simular usuários;
- implementado Logar como para staff autorizado, com preservação do ator original;
- simulação funciona em modo somente leitura e bloqueia todas as ações de escrita;
- impedida a simulação de superusuários, contas inativas e do próprio ator;
- criados registros permanentes de sessões de simulação e eventos técnicos;
- adicionada área Auditoria e suporte na Central de Cadastros;
- botão Importar do SIG e ação Logar como integrados ao grid padronizado de usuários;
- adicionadas migrations, testes de autorização, importação, isolamento e bloqueio de escrita.

## 0.6.0 — Central de Cadastros

- criado um único acesso de menu para a Central de Cadastros;
- áreas apresentadas em cards conforme as permissões do usuário;
- criada infraestrutura declarativa e reutilizável para grids e formulários;
- pesquisa dinâmica com atraso controlado e atualização parcial da tabela;
- filtros avançados recolhíveis, com contador de filtros ativos;
- ordenação segura por colunas e estado preservado na URL;
- paginação e seleção de 10, 25, 50 ou 100 registros por página;
- formulários padronizados em cards e auditoria de criação/alteração;
- telas próprias para comissões, membros, níveis, requisitos, itens e checklist;
- configuração do prazo de triagem migrada para a interface operacional;
- pessoas, servidores e vínculos disponíveis em grids somente para consulta;
- perfis de acesso atribuídos pela própria tela de usuários;
- grupos operacionais criados e atualizados pela seed idempotente;
- Django Admin mantido como retaguarda técnica para superusuários;
- tela Meus requerimentos restringida sempre ao usuário autenticado;
- adicionados testes de autorização, cards, grid dinâmico, CRUD, auditoria e isolamento dos requerimentos.

## 0.5.0 — triagem documental

- criada fila de triagem para administradores e membros vigentes da comissão;
- associação automática do requerimento à comissão vigente na submissão;
- criado checklist de triagem configurável e sem dependência de ciclos;
- preservados snapshots dos itens do checklist em cada rodada;
- implementados resultados conforme, não conforme e não aplicável;
- implementado encaminhamento para análise quando não há pendências;
- implementada devolução ao servidor para correção;
- prazo de correção configurável em 10, 30 ou 90 dias;
- prazo registrado como snapshot sem ação automática no vencimento;
- orientação consolidada obrigatória quando houver pendência;
- nova submissão após correção preserva a comissão e cria histórico correto;
- permissões consideram vigência da comissão e do mandato do membro;
- menu de triagem exibido somente para usuários autorizados;
- corrigidos metadados de versão do pacote.

## 0.4.4

- confirmação obrigatória antes de remover item, comprovante salvo ou upload temporário;
- mensagens explícitas de irreversibilidade;
- falha na exclusão assíncrona mantém o arquivo na tela.

## 0.4.3

- upload assíncrono imediato com progresso por arquivo;
- armazenamento temporário por até 24 horas;
- múltiplos comprovantes por item e limpeza de temporários abandonados.

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
