CHECKLIST_TRIAGEM = [
    {
        "codigo": "T-01",
        "titulo": "Identificação e vínculo funcional",
        "descricao": (
            "Confirmar a identificação do requerente e o vínculo funcional utilizado "
            "no pedido."
        ),
        "ordem": 1,
        "confere_comprovantes": False,
    },
    {
        "codigo": "T-02",
        "titulo": "Nível de RSC pretendido",
        "descricao": (
            "Verificar se o nível selecionado está claramente indicado no requerimento."
        ),
        "ordem": 2,
        "confere_comprovantes": False,
    },
    {
        "codigo": "T-03",
        "titulo": "Itens de pontuação informados",
        "descricao": (
            "Confirmar a existência de itens pontuados e quantidades declaradas "
            "maiores que zero."
        ),
        "ordem": 3,
        "confere_comprovantes": False,
    },
    {
        "codigo": "T-04",
        "titulo": "Comprovantes obrigatórios anexados",
        "descricao": (
            "Conferir se cada item que exige comprovação possui ao menos um "
            "documento anexado."
        ),
        "ordem": 4,
        "confere_comprovantes": True,
    },
    {
        "codigo": "T-05",
        "titulo": "Legibilidade e integridade dos documentos",
        "descricao": (
            "Verificar se os arquivos podem ser abertos e apresentam conteúdo "
            "legível e completo."
        ),
        "ordem": 5,
        "confere_comprovantes": True,
    },
    {
        "codigo": "T-06",
        "titulo": "Requisitos mínimos de submissão",
        "descricao": (
            "Confirmar o atendimento à quantidade mínima de itens e aos requisitos "
            "obrigatórios do nível."
        ),
        "ordem": 6,
        "confere_comprovantes": False,
    },
]
