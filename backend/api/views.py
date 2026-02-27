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
        
        start_time = time.time()
        
        # 1. Generate bot response
        bot_response = generate_chat_response(user_message)
        
        # 2. Classify trace
        category = classify_trace(user_message, bot_response)
        
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        # 3. Save Trace
        trace = Trace.objects.create(
            user_message=user_message,
            bot_response=bot_response,
            category=category,
            response_time_ms=response_time_ms
        )
        
        response_serializer = TraceSerializer(trace)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

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
