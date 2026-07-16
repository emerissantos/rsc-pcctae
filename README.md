# Sistema RSC-PCCTAE — UFSB

Versão **0.7.1**, com autorização operacional de triagem separada do acesso técnico e administrativo.

## Escopo desta versão

O sistema foi simplificado para o fluxo operacional do RSC-PCCTAE:

- autenticação institucional OAuth2/SIGAuth;
- sincronização do usuário, pessoa, servidor e vínculos funcionais pelas APIs da UFSB;
- cadastro de comissões e membros com vigência e histórico;
- requisitos, níveis e itens de pontuação;
- seed idempotente baseada no Decreto nº 13.048/2026;
- requerimentos apresentados a qualquer tempo, sem ciclos;
- preenchimento por **item + quantidade**;
- cálculo automático da pontuação;
- múltiplos anexos por item;
- observação opcional;
- revisão e submissão;
- distribuição automática para a comissão vigente;
- fila de triagem para membros ativos da comissão;
- checklist configurável com histórico por snapshots;
- devolução para correção com prazo configurável de 10, 30 ou 90 dias;
- snapshots da regra usada no lançamento, preservando o histórico;
- Central de Cadastros com cards por área e visibilidade baseada em permissões;
- grids reutilizáveis com pesquisa dinâmica, filtros recolhíveis, ordenação e paginação;
- perfis operacionais atribuídos pela própria interface, sem dependência cotidiana do Django Admin;
- importação administrativa de usuários do SIG, sem exigir primeiro login;
- simulação auditada de usuários em modo somente leitura para suporte técnico;
- área de auditoria com histórico de importações, simulações e ações bloqueadas;
- interface responsiva inspirada nas capturas de referência fornecidas.

Não há módulo de normas, versões normativas, matrizes ou ciclos de avaliação.

## Regra de cálculo

Cada lançamento usa apenas:

```text
pontuação = quantidade × pontos do item
```

Quando houver limite configurado no item:

```text
pontuação = mínimo(quantidade × pontos do item, limite)
```

Datas, portarias, períodos e demais detalhes não são transcritos para campos estruturados. Eles devem constar no documento comprobatório e serão conferidos pela comissão.

Nos quatro itens do requisito V, as condições de titular e substituto foram transformadas em itens independentes, por exemplo:

- `V.1-T` — CD-02 como titular;
- `V.1-S` — CD-02 como substituto.


## Comprovantes e privacidade

Cada item possui um único lançamento de quantidade e pode receber **um ou vários comprovantes**:

- use um arquivo quando ele comprovar toda a quantidade declarada;
- use vários arquivos quando a comprovação estiver dividida entre documentos;
- a comissão avalia o conjunto de anexos do item contra a quantidade informada.

Os arquivos são armazenados internamente no padrão:

```text
requerimentos/
└── <NUMERO-DO-REQUERIMENTO>/
    └── requisito-<CODIGO>/
        └── item-<CODIGO>/
            └── <UUID>-<nome-normalizado>.<extensão>
```

O caminho físico não contém SIAPE, CPF ou outro identificador funcional do servidor.

Não existe acesso direto por `/media/` ou por URL do storage. O usuário clica no documento dentro do sistema; a aplicação verifica sessão e permissão antes de entregar o conteúdo. Em produção, o Nginx usa uma localização `internal`, inacessível diretamente pela internet.

Podem consultar um comprovante:

- o requerente proprietário do pedido;
- usuários administrativos;
- membros ativos da comissão associada ao requerimento.

Membros da comissão podem consultar, mas não editar os itens declarados pelo servidor.

## Validação da quantidade

Itens configurados como inteiros aceitam somente `1`, `2`, `3` etc. A interface bloqueia separadores decimais, inclusive no Firefox, e o backend repete a validação. Portanto, valores como `1.01` ou `1,5` são rejeitados mesmo que o navegador tente enviá-los.


## Fluxo de triagem

Após a submissão, o sistema associa o requerimento à comissão vigente. O acesso à fila é permitido a membros com comissão e mandato ativos, a superusuários ou a usuários com o perfil explícito **Operação de Triagem**. O atributo `is_staff` não concede acesso ao processo.

A triagem funciona por rodadas:

1. o membro inicia a triagem;
2. o sistema cria o checklist ativo com snapshots dos textos e regras;
3. cada item é marcado como conforme, não conforme ou não aplicável;
4. havendo pendência, a orientação consolidada é obrigatória;
5. o requerimento retorna ao servidor como **Pendente de correção**;
6. o servidor ajusta os itens e submete novamente, iniciando nova rodada;
7. sem pendências, o requerimento segue para **Em análise**.

O prazo para correção é definido em **Cadastros → Triagem → Configuração da triagem** e pode ser de 10, 30 ou 90 dias. O vencimento não altera automaticamente a situação do processo; a gestão permanece com a presidência da comissão.

## Central de Cadastros e perfis de acesso

O menu principal possui somente o item **Cadastros**. A página central distribui os recursos em cards de **Pessoas e acessos**, **Comissões**, **Pontuação**, **Triagem** e **Auditoria e suporte**. Cada card e cada operação são exibidos conforme as permissões do usuário.

As listagens compartilham a mesma infraestrutura: pesquisa com atualização dinâmica, filtros avançados recolhidos, ordenação por colunas, paginação, quantidade de linhas por página, badges, estado vazio e formulários em cards. Pesquisa, filtros, ordenação e página permanecem na URL.

Os dados de pessoas, servidores e vínculos funcionais são somente para consulta, pois a fonte oficial continua sendo a API institucional. Comissões, membros, níveis, requisitos, itens de pontuação, checklist e prazo da triagem possuem telas operacionais próprias.

Perfis disponíveis:

- **Administradores do RSC-PCCTAE**;
- **Gestão de Pessoas e Acessos**;
- **Gestão de Comissões**;
- **Gestão de Pontuação**;
- **Gestão de Triagem**;
- **Consulta de Cadastros**.

A atribuição é feita em **Cadastros → Pessoas e acessos → Usuários**. O perfil administrativo não amplia a tela **Meus requerimentos**: ela continua mostrando exclusivamente os requerimentos do usuário autenticado. As filas de trabalho da comissão permanecem em telas operacionais próprias.

O Django Admin continua disponível como retaguarda técnica apenas para superusuários.

## Importação de usuários e suporte técnico

Em **Cadastros → Pessoas e acessos → Usuários**, usuários autorizados podem consultar uma conta pelo login institucional, ID do usuário ou ID institucional da pessoa. A importação cria ou atualiza:

- pessoa institucional;
- servidor;
- todos os vínculos funcionais retornados pela API;
- identidade externa;
- conta local com senha inutilizável.

A autenticação continua sendo exclusivamente pelo OAuth institucional. A importação não define senha local e não presume dados ausentes na API. Para evitar ambiguidades, prefira o login ou o ID do usuário; um ID institucional que corresponda a mais de uma conta será rejeitado.

A ação **Logar como** aparece na grade de usuários somente para contas staff que também possuam a permissão específica de simulação. A sessão:

- preserva o usuário técnico original;
- assume a visão e as permissões do usuário selecionado;
- funciona somente para leitura;
- bloqueia POST, PUT, PATCH e DELETE;
- não permite simular superusuários;
- registra ator, alvo, justificativa, data, IP, navegador e request ID;
- exibe um aviso fixo com a opção **Encerrar simulação**.

Os registros ficam disponíveis em **Cadastros → Auditoria e suporte**.

## Requisitos técnicos

- Docker 24 ou superior;
- Docker Compose v2;
- acesso aos endpoints de homologação ou produção da UFSB;
- credenciais OAuth de login;
- credenciais técnicas das APIs e `x-api-key`.

## Instalação limpa

### 1. Extraia o projeto

```bash
unzip rsc-pcctae-v0.7.1.zip
cd rsc-pcctae-v0.7.1/rsc-pcctae
```

### 2. Crie o `.env`

```bash
cp .env.example .env
```

Preencha, no mínimo:

```env
DJANGO_SECRET_KEY=uma-chave-segura
POSTGRES_PASSWORD=uma-senha-segura

UFSB_AUTH_CLIENT_ID=
UFSB_AUTH_CLIENT_SECRET=
UFSB_AUTH_USERINFO_API_KEY=

UFSB_API_CLIENT_ID=
UFSB_API_CLIENT_SECRET=
UFSB_API_KEY=
```

Mantenha todos os endpoints no mesmo ambiente: homologação com homologação ou produção com produção.

### 3. Suba os serviços

```bash
docker compose up -d --build
```

Na primeira inicialização, o container executa automaticamente:

```text
python manage.py migrate --noinput
python manage.py seed_rsc
python manage.py collectstatic --noinput
```

A seed é idempotente e pode ser executada em todas as inicializações sem duplicar registros.

### 4. Acompanhe os logs

```bash
docker compose logs -f web
```

### 5. Acesse

```text
http://127.0.0.1:8000/
```

## Tornar o primeiro usuário administrador

Faça o primeiro login pelo SIGAuth. Depois execute, substituindo o login:

```bash
docker compose exec web python manage.py shell -c "
from apps.contas.models import Usuario
u = Usuario.objects.get(username='SEU_LOGIN')
u.is_staff = True
u.is_superuser = True
u.save(update_fields=['is_staff', 'is_superuser'])
print('Administrador habilitado:', u.username)
"
```

O painel administrativo estará disponível em:

```text
http://127.0.0.1:8000/admin/
```

## Comandos úteis

```bash
# Estado dos containers
docker compose ps

# Logs
docker compose logs -f web

# Verificações
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run

# Executar novamente a seed
docker compose exec web python manage.py seed_rsc

# Testes
docker compose exec web pytest

# Lint
docker compose exec web ruff check .

# Shell Django
docker compose exec web python manage.py shell
```

## Reinicialização completa do ambiente

Atenção: este comando remove banco, Redis, arquivos enviados e estáticos persistidos nos volumes do Compose.

```bash
docker compose down -v --remove-orphans
docker compose up -d --build
```

## Estrutura principal

```text
apps/
├── contas/          autenticação e usuário local
├── integracoes/     OAuth2 e APIs institucionais
├── pessoas/         pessoa, servidor e vínculos
├── pontuacao/       níveis, requisitos, itens e seed
├── comissoes/       comissões e membros
├── requerimentos/   pedidos, lançamentos, anexos e histórico
├── triagem/          checklist, prazos e encaminhamento à análise
├── cadastros/        cards, permissões e CRUD estrutural reutilizável
├── auditoria/       base para eventos de auditoria
└── core/            infraestrutura comum e dashboard
```

## Documentação

- `docs/integracao-ufsb.md`
- `docs/modelo-simplificado-rsc.md`
- `docs/padroes-interface-requerimento.md`
- `docs/central-cadastros.md`
- `docs/referencias-ui/`

## Upload assíncrono de comprovantes

Na tela de itens, a seleção de arquivos inicia o envio imediatamente. Cada arquivo mostra o progresso individual e o botão **Salvar item** permanece desabilitado enquanto houver upload em andamento, falha de envio, quantidade inválida ou ausência de comprovante obrigatório.

Os arquivos permanecem temporariamente por até 24 horas. Ao salvar o item, são vinculados ao lançamento e armazenados em:

```text
media/requerimentos/RSC-AAAA-NNNNNN/requisito-{codigo}/item-{codigo}/{uuid}-{nome-seguro}
```

Para limpar uploads abandonados:

```bash
python manage.py limpar_uploads_temporarios
```
