import time
from rest_framework import viewsets, mixins, views, status
from rest_framework.response import Response
from django.db.models import Count, Avg
from .models import Trace
from .serializers import TraceSerializer, TraceCreateSerializer
from .llm_utils import generate_chat_response, classify_trace

class TraceViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Trace.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TraceCreateSerializer
        return TraceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_message = serializer.validated_data['user_message']
        bot_response = serializer.validated_data['bot_response']
        response_time_ms = serializer.validated_data.get('response_time_ms', 0)
        
        category = classify_trace(user_message, bot_response)
        
        trace = Trace.objects.create(
            user_message=user_message,
            bot_response=bot_response,
            category=category,
            response_time_ms=response_time_ms
        )
        
        response_serializer = TraceSerializer(trace)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ChatView(views.APIView):
    def post(self, request, *args, **kwargs):
        user_message = request.data.get('user_message')
        if not user_message:
            return Response({'error': 'user_message is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        start_time = time.time()
        bot_response = generate_chat_response(user_message)
        end_time = time.time()
        
        response_time_ms = int((end_time - start_time) * 1000)
        
        return Response({
            'bot_response': bot_response,
            'response_time_ms': response_time_ms
        })

class AnalyticsView(views.APIView):
    def get(self, request, *args, **kwargs):
        total_traces = Trace.objects.count()
        
        avg_response_time = Trace.objects.aggregate(avg_time=Avg('response_time_ms'))['avg_time']
        avg_response_time = round(avg_response_time, 2) if avg_response_time is not None else 0
        
        category_counts = Trace.objects.values('category').annotate(count=Count('category')).order_by('-count')
        
        breakdown = []
        for item in category_counts:
            percentage = round((item['count'] / total_traces) * 100, 2) if total_traces > 0 else 0
            breakdown.append({
                'category': item['category'],
                'count': item['count'],
                'percentage': percentage
            })
            
        return Response({
            'total_traces': total_traces,
            'average_response_time_ms': avg_response_time,
            'category_breakdown': breakdown
        })
