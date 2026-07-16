# Generated manually for the project foundation.
import uuid

import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("nome_exibicao", models.CharField(blank=True, max_length=255, verbose_name="nome de exibição")),
                ("primeiro_acesso_em", models.DateTimeField(blank=True, null=True, verbose_name="primeiro acesso em")),
                ("ultimo_acesso_em", models.DateTimeField(blank=True, null=True, verbose_name="último acesso em")),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "usuário",
                "verbose_name_plural": "usuários",
                "ordering": ["username"],
            },
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
        migrations.CreateModel(
            name="IdentidadeExterna",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("provedor", models.CharField(default="sigauth_ufsb", max_length=50)),
                ("id_usuario_externo", models.BigIntegerField(verbose_name="ID do usuário externo")),
                ("id_institucional", models.BigIntegerField(blank=True, null=True, verbose_name="ID institucional")),
                ("login", models.CharField(max_length=150)),
                ("id_unidade_origem", models.BigIntegerField(blank=True, null=True)),
                ("ativo_na_origem", models.BooleanField(default=True)),
                ("email_recebido", models.EmailField(blank=True, max_length=254)),
                ("nome_recebido", models.CharField(blank=True, max_length=255)),
                ("ultimo_login_em", models.DateTimeField(blank=True, null=True)),
                ("ultima_sincronizacao_em", models.DateTimeField(blank=True, null=True)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="identidades_externas", to="contas.usuario")),
            ],
            options={
                "verbose_name": "identidade externa",
                "verbose_name_plural": "identidades externas",
                "ordering": ["provedor", "login"],
                "indexes": [
                    models.Index(fields=["id_institucional"], name="idx_identidade_institucional"),
                    models.Index(fields=["login"], name="idx_identidade_login"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("provedor", "id_usuario_externo"), name="uniq_identidade_provedor_usuario"),
                ],
            },
        ),
    ]
