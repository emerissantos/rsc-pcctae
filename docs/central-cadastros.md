# Central de Cadastros

## Objetivo

Substituir o uso cotidiano do Django Admin por telas operacionais integradas à identidade visual do RSC-PCCTAE, sem transformar o menu principal em uma relação extensa de modelos.

## Organização

A rota `/cadastros/` apresenta cards de áreas. Dentro de cada área, novos cards levam aos recursos autorizados:

- Pessoas e acessos;
- Comissões;
- Pontuação;
- Triagem.

## Infraestrutura reutilizável

As definições dos recursos ficam em `apps/cadastros/registry.py`. Cada recurso declara:

- model;
- área;
- colunas;
- campos pesquisáveis;
- filtros;
- campos ordenáveis;
- relacionamentos otimizados;
- formulário;
- seções visuais;
- operações permitidas.

As views, templates, paginação, pesquisa, filtros, ordenação, auditoria e comportamento dinâmico são compartilhados. Um novo cadastro normalmente exige apenas uma entrada no registro e, quando necessário, um `ModelForm` específico.

## Segurança

A autorização usa as permissões nativas `view`, `add`, `change` e `delete` de cada model. Cards e botões são ocultados quando o usuário não possui a permissão, e as views repetem a validação no backend.

A seed cria os grupos:

- Administradores do RSC-PCCTAE;
- Gestão de Comissões;
- Gestão de Pontuação;
- Gestão de Triagem;
- Consulta de Cadastros.

A atribuição dos grupos é feita na tela de usuários. Usuários sincronizados, pessoas, servidores e vínculos funcionais são somente leitura porque a API institucional é a fonte oficial.

## Isolamento do requerente

`/requerimentos/` sempre filtra por `requerente=request.user`, mesmo quando o usuário também possui atribuições administrativas. O acesso operacional a processos de terceiros ocorre exclusivamente por filas específicas e com validação de comissão, mandato ou permissão administrativa.

## Grid

O grid suporta:

- pesquisa textual dinâmica;
- filtros recolhíveis;
- ordenação por lista branca de campos;
- paginação;
- 10, 25, 50 ou 100 registros por página;
- atualização parcial sem recarregar toda a tela;
- preservação do estado na query string;
- fallback por formulário GET quando JavaScript não estiver disponível.
