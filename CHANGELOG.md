# Changelog

## 0.8.3 — meus dados funcionais

- página somente leitura com identidade, servidor e vínculos funcionais;
- nome e e-mail da área autenticada direcionam para a conferência dos dados;
- orientação ao servidor para procurar o cadastro funcional da Progepe em caso de divergência;
- auditoria específica da consulta.

## 0.8.2 — impedimento de atuação no próprio requerimento

- cria regra transversal de segregação de funções para etapas operacionais;
- impede que o requerente visualize, inicie, altere ou conclua a triagem do próprio processo;
- a vedação prevalece sobre comissão ativa, permissões operacionais, `is_staff` e `is_superuser`;
- remove o próprio requerimento da fila de triagem do usuário;
- preserva o acesso do requerente à consulta, correção, histórico e comprovantes do próprio processo;
- disponibiliza função reutilizável para o futuro módulo de avaliação, relatoria e deliberação;
- adiciona testes de fila, URL direta, membro ativo, operador e superusuário.

## 0.8.1 — formulário F-00 em DOCX editável

- gera o F-00 diretamente no requerimento em formato DOCX;
- preenche dados funcionais, nível, pontuação, itens e comprovantes;
- organiza os itens pelos critérios I a VI com subtotais e total;
- destaca campos ausentes para complementação manual;
- registra a geração na auditoria e protege o download contra cache;
- adiciona python-docx, migration e testes de autorização e conteúdo.

## 0.8.0 — auditoria transversal

- amplia o evento de auditoria com categoria, nível, sucesso, recurso, objeto, método, caminho e status HTTP;
- registra login bem-sucedido, falhas do OAuth e logout;
- registra respostas 403 com ator real, usuário simulado, IP e request ID;
- registra criação, alteração e exclusão nos cadastros estruturais;
- preserva comparação automática dos valores anteriores e posteriores e a lista de campos alterados;
- registra atribuição e remoção de perfis, ativação e desativação de usuários;
- registra criação, visualização e submissão de requerimentos;
- registra itens adicionados, alterados ou removidos;
- registra uploads temporários, comprovantes vinculados, downloads e remoções;
- registra início, salvamento e conclusão de cada rodada de triagem;
- registra início, encerramento automático ou manual e tentativas bloqueadas durante simulação;
- cria tela detalhada do evento com comparação antes/depois e dados complementares;
- protege senhas, tokens e chaves e mascara CPF/CNPJ nos snapshots;
- torna os eventos somente leitura na interface e no Django Admin;
- ajusta o grupo Administradores para não receber permissões de alteração/exclusão em recursos somente leitura;
- adiciona migration e testes transversais de autenticação, autorização, CRUD, documentos e triagem.

## 0.7.3 — isolamento da Central de Cadastros

- remove definitivamente o bypass de acesso concedido por `is_staff`;
- exige vínculo a um perfil funcional próprio da Central de Cadastros;
- impede que permissões diretas residuais liberem cards ou URLs administrativas;
- impede que o perfil Operação de Triagem exponha cadastros por compartilhar permissões de consulta;
- mantém superusuário como único acesso emergencial implícito;
- cria o comando `configurar_como_requerente` para limpar perfis, permissões diretas e flags administrativas;
- adiciona testes para requerente, antigo staff, permissão residual e operador de triagem.

## 0.7.2 — histórico de triagem e comunicações

- adiciona resumo destacado das correções solicitadas no requerimento;
- exibe responsável, data de início, conclusão e usuário que concluiu a triagem;
- apresenta orientação consolidada, prazo e pendências por item do checklist;
- cria histórico visual reutilizável com todas as rodadas e movimentações do processo;
- disponibiliza o mesmo histórico na tela operacional da comissão;
- mantém observações de triagens em andamento privadas até a conclusão;
- adiciona carregamento otimizado com `select_related` e `Prefetch`;
- adiciona testes de transparência, privacidade de rascunhos e múltiplas rodadas.

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
