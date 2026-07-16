# Modelo simplificado do RSC-PCCTAE

## Decisões

1. Os pedidos podem ser apresentados a qualquer tempo; não existem ciclos.
2. O sistema não administra normas ou versões normativas.
3. Os requisitos e itens ativos são cadastros operacionais.
4. O servidor seleciona o item, informa a quantidade e anexa os comprovantes.
5. A observação é opcional.
6. O sistema calcula automaticamente a pontuação.
7. A comissão valida a quantidade e poderá ajustá-la com justificativa em etapa futura.
8. O lançamento preserva snapshots do código, descrição, unidade, pontuação e limite usados no momento do pedido.

## Entidades

```text
Requisito
└── ItemPontuacao

NivelRSC
└── requisitos obrigatórios

Requerimento
├── vínculo funcional
├── nível pretendido
├── LancamentoItem
│   └── DocumentoLancamento
└── HistoricoRequerimento
```

## Lançamento

Campos informados pelo servidor:

- item;
- quantidade;
- documentos;
- observação opcional.

Campos calculados ou preservados pelo sistema:

- pontuação declarada;
- código do item;
- descrição do item;
- unidade;
- pontos por quantidade;
- limite;
- exigência de anexo.

## Itens com valores alternativos

Para manter o preenchimento somente por item e quantidade, alternativas como titular e substituto são itens separados. Não existe campo adicional de condição.
