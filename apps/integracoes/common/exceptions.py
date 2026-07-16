class IntegrationError(Exception):
    """Erro-base de integração externa com mensagem segura para a aplicação."""

    default_message = "O serviço institucional apresentou uma falha temporária."

    def __init__(self, message: str | None = None, *, status_code: int | None = None):
        super().__init__(message or self.default_message)
        self.status_code = status_code


class IntegrationConfigurationError(IntegrationError):
    default_message = "A integração institucional não está configurada corretamente."


class IntegrationAuthenticationError(IntegrationError):
    default_message = "Não foi possível autenticar a aplicação no serviço institucional."


class IntegrationAuthorizationError(IntegrationError):
    default_message = "A aplicação não possui autorização para consultar o serviço institucional."


class IntegrationNotFoundError(IntegrationError):
    default_message = "O cadastro solicitado não foi localizado no serviço institucional."


class IntegrationRateLimitError(IntegrationError):
    default_message = "O limite temporário de consultas ao serviço institucional foi atingido."

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        reset_seconds: int | None = None,
    ):
        super().__init__(message, status_code=status_code)
        self.reset_seconds = reset_seconds


class IntegrationTimeoutError(IntegrationError):
    default_message = "O serviço institucional demorou mais do que o esperado para responder."


class IntegrationInvalidResponseError(IntegrationError):
    default_message = "O serviço institucional retornou dados em formato inesperado."
