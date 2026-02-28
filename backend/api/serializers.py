from rest_framework import serializers
from .models import Trace

class TraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trace
        fields = ['id', 'user_message', 'bot_response', 'category', 'timestamp', 'response_time_ms']
        read_only_fields = ['id', 'timestamp']

class TraceCreateSerializer(serializers.Serializer):
    user_message = serializers.CharField(required=True)
    bot_response = serializers.CharField(required=True)
    response_time_ms = serializers.IntegerField(required=False, default=0)
