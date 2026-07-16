# RSC-PCCTAE 0.7.0 — Importação institucional e suporte técnico

## Importação do SIG

- consulta exata por login institucional, ID do usuário ou ID institucional;
- sincronização de pessoa, servidor e todos os vínculos retornados;
- criação ou atualização da identidade externa e da conta local;
- senha local inutilizável e autenticação mantida exclusivamente no OAuth;
- registro do responsável e dos identificadores técnicos na auditoria.

## Logar como

- disponível somente para staff com permissão específica;
- exige justificativa técnica com no mínimo 10 caracteres;
- preserva a sessão e a identidade do usuário técnico;
- reproduz a visão e as permissões do usuário selecionado;
- funciona em modo somente leitura;
- bloqueia ações POST, PUT, PATCH e DELETE;
- não permite simular superusuários, contas inativas, o próprio ator ou sessões aninhadas;
- registra início, encerramento e tentativas de alteração bloqueadas.

## Interface e acesso

- botão **Importar do SIG** na listagem de usuários;
- ação **Logar como** por linha no grid reutilizável;
- aviso fixo durante a simulação, com identificação do ator e do alvo;
- área **Auditoria e suporte** com grids de eventos e sessões;
- novo grupo **Gestão de Pessoas e Acessos**;
- tela **Meus requerimentos** continua restrita ao usuário efetivamente simulado.
