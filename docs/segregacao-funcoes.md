# Segregação de funções no requerimento

## Regra obrigatória

O titular de um requerimento não pode praticar atos operacionais sobre o próprio processo.
A vedação é absoluta e prevalece sobre:

- participação ativa em comissão vigente;
- perfil **Operação de Triagem**;
- permissões diretas;
- `is_staff`;
- `is_superuser`.

O requerente mantém normalmente o acesso às funcionalidades próprias do servidor:
consulta, correção, inclusão e remoção de itens enquanto permitido, envio de comprovantes,
submissão, histórico e geração do F-00.

## Implementação compartilhada

A regra transversal está em:

```python
from apps.requerimentos.permissions import pode_atuar_operacionalmente
```

Todo módulo que execute análise institucional deve validar essa função antes de
qualquer outra autorização:

```python
if not pode_atuar_operacionalmente(usuario, requerimento):
    return False
```

A ordem é importante: uma permissão funcional nunca pode sobrescrever o impedimento
por identidade entre o ator e o requerente.

## Triagem

Na triagem, a regra é aplicada em quatro níveis:

1. o próprio requerimento é excluído da fila apresentada ao usuário;
2. a URL de início retorna `403`;
3. a tela operacional de uma rodada já iniciada retorna `403`;
4. salvar ou concluir a rodada retorna `403`.

A resposta `403` é registrada pela auditoria transversal como acesso negado.

## Avaliação, relatoria e deliberação

Os módulos futuros de avaliação individual, dupla relatoria, consolidação e
deliberação deverão reutilizar a mesma função. O requerente não poderá:

- ser designado avaliador do próprio processo;
- aceitar ou iniciar avaliação do próprio processo;
- registrar pontuação reconhecida ou glosa;
- emitir relatório ou voto;
- participar da deliberação do próprio requerimento.

Além do bloqueio no backend, as listas de candidatos e filas deverão excluir o
requerente para evitar seleção indevida na interface.
