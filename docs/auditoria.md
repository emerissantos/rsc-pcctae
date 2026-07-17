# Auditoria do RSC-PCCTAE

## Objetivo

A auditoria registra eventos funcionais e de segurança sem substituir o histórico específico do requerimento. O histórico explica o fluxo ao usuário; a auditoria permite rastrear quem realizou ou tentou realizar uma ação técnica ou administrativa.

## Identidade do ator

- `ator`: usuário autenticado real;
- `usuario_afetado`: titular do processo, conta alterada ou usuário simulado;
- durante `Logar como`, o ator real é preservado e o usuário simulado aparece separadamente.

## Contexto da requisição

Quando disponível, são armazenados:

- request ID;
- endereço IP, considerando `X-Forwarded-For`, `X-Real-IP` e `REMOTE_ADDR`;
- User-Agent;
- método HTTP;
- caminho;
- status HTTP;
- indicação de sucesso, falha ou bloqueio.

## Comparação de alterações

Cadastros, itens, requerimentos e triagens podem armazenar:

- dados anteriores;
- dados posteriores;
- nomes dos campos alterados;
- tipo e identificador estável do objeto.

## Proteção de dados

O serializador não registra valores de campos cujo nome indique senha, token, segredo, chave de API ou autorização. CPF e CNPJ são mascarados, mantendo apenas os quatro últimos dígitos.

A auditoria não armazena o conteúdo dos documentos. Registra apenas metadados necessários, como nome original, tamanho, MIME, hash, requerimento e item.

## Imutabilidade

Eventos são somente leitura na Central de Cadastros e no Django Admin. Não há ações operacionais para editar ou excluir eventos.

## Crescimento da tabela

Visualizações de requerimentos e downloads geram eventos. O banco deve ser monitorado e uma política institucional de retenção deve ser definida antes de qualquer limpeza automática.
