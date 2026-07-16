from .permissions import pode_acessar_fila


def permissoes_triagem(request):
    usuario = getattr(request, "user", None)
    return {"pode_acessar_triagem": bool(usuario and pode_acessar_fila(usuario))}
