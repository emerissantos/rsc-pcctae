# RSC-PCCTAE 0.8.0 — Auditoria transversal

## Escopo

A auditoria deixa de registrar apenas importações e bloqueios da simulação e passa a acompanhar os principais eventos funcionais e de segurança do sistema.

## Eventos cobertos

- login institucional bem-sucedido;
- falhas ou recusas do fluxo OAuth;
- logout;
- respostas HTTP 403;
- início, encerramento e bloqueios do recurso Logar como;
- importação de usuários do SIG;
- criação, alteração e exclusão de cadastros estruturais;
- mudanças de perfis e situação de acesso;
- criação, visualização e submissão de requerimentos;
- inclusão, alteração e remoção de itens;
- uploads temporários e comprovantes definitivos;
- download e remoção de comprovantes;
- início, salvamento e conclusão da triagem.

## Dados registrados

Cada evento pode preservar ator real, usuário afetado, data, IP, navegador, request ID, método HTTP, caminho, status HTTP, recurso, tipo e identificador do objeto, resultado, dados complementares e diferenças antes/depois.

Senhas, tokens, segredos e chaves são protegidos. CPF e CNPJ são mascarados quando aparecem em snapshots.

## Interface

O grid de eventos ganhou filtros por categoria, tipo, nível e resultado. Cada linha possui uma tela de detalhes com contexto da requisição, objeto relacionado, campos alterados e comparação dos dados.
