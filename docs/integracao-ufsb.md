# Integração OAuth2 e APIs da UFSB

## Fluxos utilizados

O sistema utiliza dois clientes OAuth2 independentes:

1. **Authorization Code**, para autenticação interativa do usuário;
2. **Client Credentials**, para consultas técnicas aos serviços institucionais.

O token do usuário é usado apenas para consultar `/public/security/v2/usuarios/me` e não é persistido no banco nem na sessão. O token técnico é mantido temporariamente no cache até próximo de sua expiração.

## Identificadores

- `id_usuario`: identifica a conta autenticada e fica em `IdentidadeExterna`;
- `id_institucional`: identifica a pessoa e fica em `PessoaInstitucional`;
- `id_servidor`: identifica cada vínculo funcional e fica em `VinculoFuncional`.

Uma pessoa pode possuir vários registros de servidor. Todos os vínculos retornados são preservados.

## Cabeçalhos das APIs

```http
Authorization: Bearer <token-tecnico>
x-api-key: <chave-da-aplicacao>
Content-Type: application/json;charset=UTF-8
Accept: application/json
```

## Segurança do `.env`

O arquivo `.env` está no `.gitignore`. Para criá-lo com segredos locais aleatórios:

```bash
python scripts/init_env.py
```

Depois, preencha manualmente:

- `UFSB_AUTH_CLIENT_ID`;
- `UFSB_AUTH_CLIENT_SECRET`;
- `UFSB_API_CLIENT_ID`;
- `UFSB_API_CLIENT_SECRET`;
- `UFSB_API_KEY`.

Em produção, o `.env` deve ter permissão `0600` e acesso restrito ao usuário que executa a aplicação. Em ambientes com cofre de segredos, as variáveis podem ser injetadas diretamente e `DJANGO_READ_DOT_ENV_FILE=false` pode ser usado.

## Callback registrado no SIGAuth

Desenvolvimento:

```text
http://127.0.0.1:8000/autenticacao/callback/
```

Produção, exemplo:

```text
https://rsc.ufsb.edu.br/autenticacao/callback/
```

A URI deve coincidir exatamente com a registrada no provedor.

## Parâmetros de consulta configuráveis

Como os parâmetros aceitos pelo gateway podem variar, os nomes ficam no `.env`:

```env
UFSB_API_USUARIOS_ID_USUARIO_PARAM=id-usuario
UFSB_API_USUARIOS_LOGIN_PARAM=login
UFSB_API_USUARIOS_ID_INSTITUCIONAL_PARAM=id-institucional
UFSB_API_SERVIDORES_ID_INSTITUCIONAL_PARAM=id-institucional
```

## Rate limit e paginação

O cliente interpreta:

- `RateLimit-Limit`;
- `RateLimit-Remaining`;
- `RateLimit-Reset`;
- `X-RateLimit-Limit-Hour`;
- `X-RateLimit-Remaining-Hour`;
- `X-Pages`;
- `X-Total`.

Ao receber HTTP 429, a operação falha de forma controlada sem apagar dados locais já sincronizados.

## PKCE

O suporte a PKCE está implementado, mas desabilitado por padrão por compatibilidade com o provedor legado:

```env
UFSB_AUTH_USE_PKCE=false
```

Ative somente depois de confirmar suporte no SIGAuth.
