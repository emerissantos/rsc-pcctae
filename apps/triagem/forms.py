from django import forms

from .models import TriagemRequerimento, VerificacaoChecklistTriagem


class VerificacaoChecklistForm(forms.ModelForm):
    class Meta:
        model = VerificacaoChecklistTriagem
        fields = ("situacao", "observacao")
        widgets = {
            "situacao": forms.Select(attrs={"class": "form-select"}),
            "observacao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Registre a pendência ou uma observação objetiva.",
                }
            ),
        }


class TriagemConclusaoForm(forms.ModelForm):
    class Meta:
        model = TriagemRequerimento
        fields = ("orientacao_correcao",)
        widgets = {
            "orientacao_correcao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Informe de forma consolidada o que o servidor deverá corrigir. "
                        "O prazo será aplicado somente quando houver pendência."
                    ),
                }
            )
        }
