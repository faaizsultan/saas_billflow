from django.contrib import admin
from .models import Trace

@admin.register(Trace)
class TraceAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'timestamp', 'response_time_ms')
    list_filter = ('category', 'timestamp')
    search_fields = ('user_message', 'bot_response', 'id')
    readonly_fields = ('id', 'timestamp')
    ordering = ('-timestamp',)
