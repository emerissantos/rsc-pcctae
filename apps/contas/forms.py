from django import forms


class JustificativaImpersonacaoForm(forms.Form):
    justificativa = forms.CharField(
        label="Justificativa técnica",
        min_length=10,
        max_length=500,
        help_text=(
            "Descreva o chamado, incidente ou verificação que exige a simulação. "
            "A justificativa ficará registrada permanentemente."
        ),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": (
                    "Ex.: chamado GLPI 12345 — reproduzir erro na revisão do requerimento."
                ),
            }
        ),
    )
