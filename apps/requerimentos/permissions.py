from __future__ import annotations


def usuario_e_requerente(usuario, requerimento) -> bool:
    """Indica se o usuário é o titular do requerimento informado."""
    if not getattr(usuario, "is_authenticated", False):
        return False
    return requerimento.requerente_id == usuario.pk


def pode_atuar_operacionalmente(usuario, requerimento) -> bool:
    """Regra transversal de segregação de funções.

    O titular nunca pode praticar atos de triagem, avaliação, relatoria,
    deliberação ou outra análise operacional sobre o próprio requerimento.
    A vedação prevalece sobre participação em comissão, permissões explícitas,
    ``is_staff`` e ``is_superuser``.
    """
    if not getattr(usuario, "is_authenticated", False):
        return False
    return not usuario_e_requerente(usuario, requerimento)
