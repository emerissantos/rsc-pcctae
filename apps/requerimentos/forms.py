from decimal import Decimal, InvalidOperation

from django import forms

from apps.pessoas.models import VinculoFuncional
from apps.pontuacao.models import NivelRSC

from .models import Requerimento


class RequerimentoForm(forms.ModelForm):
    class Meta:
        model = Requerimento
        fields = ("vinculo", "nivel_pretendido", "observacao_geral")
        widgets = {
            "observacao_geral": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nivel_pretendido"].queryset = NivelRSC.objects.filter(ativo=True)
        self.fields["vinculo"].queryset = VinculoFuncional.objects.none()
        if usuario and usuario.is_authenticated:
            pessoas_ids = usuario.identidades_externas.exclude(pessoa=None).values_list(
                "pessoa_id", flat=True
            )
            self.fields["vinculo"].queryset = VinculoFuncional.objects.filter(
                servidor__pessoa_id__in=pessoas_ids,
                ativo=True,
            ).select_related("servidor")
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["vinculo"].widget.attrs["class"] = "form-select"
        self.fields["nivel_pretendido"].widget.attrs["class"] = "form-select"


def limpar_quantidade(valor: str) -> Decimal:
    try:
        quantidade = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise forms.ValidationError("Informe uma quantidade válida.") from exc
    if quantidade <= 0:
        raise forms.ValidationError("Informe uma quantidade maior que zero.")
    return quantidade
