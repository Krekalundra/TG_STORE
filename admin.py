from django.contrib import admin
from .models.settings import TelegramSettings
from .models.operators import Operator

@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    list_display = ('token', 'chat_id')
    fields = ('token', 'chat_id')

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('username',)