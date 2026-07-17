# Geração do F-00 em DOCX

O sistema gera uma cópia editável do **F-00 — Formulário-padrão de requerimento do RSC-PCCTAE** a partir do estado atual do requerimento.

## Acesso

O botão está disponível:

- no detalhe do requerimento;
- na etapa de revisão e submissão.

A rota exige autenticação e aplica a mesma autorização usada para visualizar o requerimento. O requerente acessa somente o próprio processo; membros e operadores acessam apenas quando possuírem competência sobre o requerimento.

## Informações preenchidas automaticamente

- nome do servidor;
- SIAPE e dígito;
- cargo;
- data de ingresso;
- lotação;
- e-mail institucional;
- nível de RSC pretendido;
- pontuação mínima;
- pontuação total apresentada;
- quantidade de critérios específicos;
- pontuação excedente;
- itens agrupados nos requisitos I a VI;
- quantidade e unidade de medida;
- pontuação unitária e pontuação obtida;
- observação do requerente;
- nomes dos comprovantes, numerados como `DOC-001`, `DOC-002` etc.;
- subtotais por requisito e total geral.

## Campos para complementação

Quando a base não possui a informação, o DOCX apresenta um marcador editável:

```text
[PREENCHER]
[PREENCHER, SE HOUVER]
```

Atualmente isso se aplica principalmente a:

- nível de classificação A a E;
- telefone;
- função ou encargo;
- saldo de concessão anterior;
- número do processo da concessão anterior.

## Características do arquivo

- formato Office Open XML (`.docx`);
- documento totalmente editável;
- páginas A4 em orientação retrato;
- tabelas com cabeçalho repetido quando houver quebra de página;
- linhas adicionais para inclusão manual;
- metadados institucionais, sem autor pessoal;
- resposta privada e sem cache.

## Auditoria

Cada geração cria o evento `FORMULARIO_F00_GERADO`, contendo:

- ator real;
- usuário requerente;
- requerimento relacionado;
- situação do processo;
- quantidade de itens e comprovantes;
- nome do arquivo;
- IP, navegador e request ID.
