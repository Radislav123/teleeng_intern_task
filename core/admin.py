from typing import Type

import django.forms.models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from core import models as core_models
from core.settings import Settings
from logger import Logger


def register_models(model_admins: list[Type["CoreAdmin"]]) -> None:
    for model_admin in model_admins:
        admin.site.register(model_admin.model, model_admin)


class CoreAdmin(admin.ModelAdmin):
    model = core_models.CoreModel
    settings = Settings()
    hidden_fields = ()
    _fieldsets = ()
    # {вставляемое_поле: поле_перед_которым_вставляется}
    # {field: None} - вставится последним
    extra_list_display: dict[str, str] = {}
    not_required_fields = ()
    not_show_list = ()
    reorder_fields: dict[str, str] = {}

    def __init__(self, model, admin_site):
        self.logger = Logger(self.__class__.__name__)

        self.list_display = [field for field in self._list_display if field not in self.hidden_fields]
        for field, before_field in self.extra_list_display.items():
            if before_field is None:
                self.list_display.append(field)
            else:
                self.list_display.insert(self.list_display.index(before_field), field)

        for field, before_field in self.reorder_fields.items():
            self.list_display.remove(field)
            if before_field is None:
                self.list_display.append(field)
            else:
                self.list_display.insert(self.list_display.index(before_field), field)

        self.list_display = tuple(x for x in self.list_display if x not in self.not_show_list)
        if self.fieldsets is not None:
            self.fieldsets += self._fieldsets
        else:
            self.fieldsets = self._fieldsets

        super().__init__(model, admin_site)

    def get_form(self, request, obj = None, **kwargs) -> django.forms.models.ModelFormMetaclass:
        form = super().get_form(request, obj, **kwargs)
        for field_name in self.not_required_fields:
            form.base_fields[field_name].required = False
        return form

    @property
    def _list_display(self) -> tuple:
        # noinspection PyProtectedMember
        return tuple(field.name for field in self.model._meta.fields)


class UserAdmin(CoreAdmin, DjangoUserAdmin):
    model = core_models.User
    hidden_fields = ("password",)
    _fieldsets = (
        (
            "Telegram",
            {"fields": ("telegram_user_id", "telegram_chat_id")}
        ),
    )


model_admins_to_register = [UserAdmin]
register_models(model_admins_to_register)
