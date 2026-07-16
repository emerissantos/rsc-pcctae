from __future__ import annotations


def pode_importar_usuario_sig(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return user.is_superuser or user.has_perm("contas.importar_usuario_sig")


def pode_simular_usuario(user) -> bool:
    if not getattr(user, "is_authenticated", False) or not user.is_staff:
        return False
    return user.is_superuser or user.has_perm("contas.simular_usuario")


def usuario_pode_ser_simulado(ator, alvo) -> bool:
    if not pode_simular_usuario(ator):
        return False
    if not alvo or not alvo.is_active or alvo.pk == ator.pk:
        return False
    return not alvo.is_superuser
