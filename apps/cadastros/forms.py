from __future__ import annotations

from django import forms
from django.db import models

from apps.comissoes.models import Comissao, MembroComissao
from apps.contas.models import Usuario
from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito
from apps.triagem.models import ConfiguracaoTriagem, ItemChecklistTriagem


class CadastroModelForm(forms.ModelForm):
    """Base visual única para os formulários da Central de Cadastros."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 4)


MANAGED_GROUP_NAMES = (
    "Administradores do RSC-PCCTAE",
    "Gestão de Pessoas e Acessos",
    "Gestão de Comissões",
    "Gestão de Pontuação",
    "Gestão de Triagem",
    "Operação de Triagem",
    "Consulta de Cadastros",
)


class UsuarioAcessoForm(CadastroModelForm):
    class Meta:
        model = Usuario
        fields = ("is_active", "groups")
        widgets = {"groups": forms.CheckboxSelectMultiple()}
        labels = {
            "is_active": "Acesso ativo",
            "groups": "Perfis de acesso",
        }
        help_texts = {
            "groups": (
                "Os perfis controlam quais cards, cadastros e operações ficam disponíveis. "
                "O usuário requerente continua vendo somente os próprios requerimentos."
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = (
            self.fields["groups"].queryset.filter(name__in=MANAGED_GROUP_NAMES).order_by("name")
        )


class ComissaoForm(CadastroModelForm):
    class Meta:
        model = Comissao
        fields = (
            "nome",
            "sigla",
            "ato_designacao",
            "inicio_vigencia",
            "fim_vigencia",
            "ativa",
            "observacoes",
        )
        widgets = {
            "inicio_vigencia": forms.DateInput(attrs={"type": "date"}),
            "fim_vigencia": forms.DateInput(attrs={"type": "date"}),
        }


class MembroComissaoForm(CadastroModelForm):
    class Meta:
        model = MembroComissao
        fields = (
            "comissao",
            "usuario",
            "nome_snapshot",
            "email_snapshot",
            "papel",
            "inicio_mandato",
            "fim_mandato",
            "ativo",
        )
        widgets = {
            "inicio_mandato": forms.DateInput(attrs={"type": "date"}),
            "fim_mandato": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "usuario": (
                "Vincule ao usuário do sistema quando disponível. Para preservar o histórico, "
                "o nome e o e-mail permanecem registrados como fotografia do mandato."
            ),
            "nome_snapshot": "Obrigatório apenas quando não houver usuário vinculado.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome_snapshot"].required = False
        self.fields["usuario"].queryset = self.fields["usuario"].queryset.order_by("username")

    def clean(self):
        cleaned = super().clean()
        usuario = cleaned.get("usuario")
        nome = (cleaned.get("nome_snapshot") or "").strip()
        if usuario and not nome:
            cleaned["nome_snapshot"] = str(usuario)
        if usuario and not cleaned.get("email_snapshot"):
            cleaned["email_snapshot"] = usuario.email
        if not cleaned.get("nome_snapshot"):
            self.add_error(
                "nome_snapshot",
                "Informe o nome do membro ou selecione um usuário do sistema.",
            )
        return cleaned


class RequisitoForm(CadastroModelForm):
    class Meta:
        model = Requisito
        fields = ("codigo", "nome", "descricao", "ordem", "ativo")


class ItemPontuacaoForm(CadastroModelForm):
    class Meta:
        model = ItemPontuacao
        fields = (
            "requisito",
            "codigo",
            "descricao",
            "unidade",
            "pontos_por_quantidade",
            "limite_pontos",
            "tipo_quantidade",
            "exige_anexo",
            "observacao_permitida",
            "orientacao",
            "ordem",
            "ativo",
        )


class NivelRSCForm(CadastroModelForm):
    class Meta:
        model = NivelRSC
        fields = (
            "codigo",
            "nome",
            "descricao",
            "pontuacao_minima",
            "quantidade_minima_itens",
            "ordem",
            "ativo",
            "requisitos_obrigatorios",
        )
        widgets = {
            "requisitos_obrigatorios": forms.CheckboxSelectMultiple(),
        }


class ItemChecklistTriagemForm(CadastroModelForm):
    class Meta:
        model = ItemChecklistTriagem
        fields = (
            "codigo",
            "titulo",
            "descricao",
            "ordem",
            "obrigatorio",
            "confere_comprovantes",
            "ativo",
        )


class ConfiguracaoTriagemForm(CadastroModelForm):
    class Meta:
        model = ConfiguracaoTriagem
        fields = ("prazo_correcao_dias",)


class ImportarUsuarioSIGForm(forms.Form):
    class Identificador(models.TextChoices):
        LOGIN = "login", "Login institucional"
        ID_USUARIO = "id_usuario", "ID do usuário"
        ID_INSTITUCIONAL = "id_institucional", "ID institucional da pessoa"

    tipo_identificador = forms.ChoiceField(
        label="Identificador para consulta",
        choices=Identificador.choices,
        initial=Identificador.LOGIN,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    valor = forms.CharField(
        label="Valor",
        max_length=150,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
                "placeholder": "Informe o login ou identificador institucional",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo_identificador")
        valor = (cleaned.get("valor") or "").strip()
        if tipo in {self.Identificador.ID_USUARIO, self.Identificador.ID_INSTITUCIONAL}:
            try:
                cleaned["valor_numerico"] = int(valor)
            except (TypeError, ValueError):
                self.add_error("valor", "Informe um identificador numérico válido.")
        elif tipo == self.Identificador.LOGIN:
            cleaned["valor"] = valor.lower()
        return cleaned

    def service_kwargs(self) -> dict[str, object]:
        tipo = self.cleaned_data["tipo_identificador"]
        if tipo == self.Identificador.LOGIN:
            return {"login": self.cleaned_data["valor"]}
        return {tipo: self.cleaned_data["valor_numerico"]}
