class BusinessRuleError(Exception):
    """Erro esperado de regra de negócio."""


class PermissionDeniedError(BusinessRuleError):
    """A ação não é permitida no contexto informado."""
