from .permissions import pode_acessar_cadastros


def acesso_cadastros(request):
    return {
        "pode_acessar_cadastros": pode_acessar_cadastros(request.user),
    }
