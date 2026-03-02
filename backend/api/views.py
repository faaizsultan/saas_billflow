import time
from rest_framework import viewsets, mixins, views, status
from rest_framework.response import Response
from django.db.models import Count, Avg
from django.conf import settings
from .models import Trace
from django.db import connection
from django.db.utils import OperationalError, InterfaceError
from .serializers import TraceSerializer, TraceCreateSerializer
from .llm_utils import generate_chat_response, classify_trace
import logging
import google.generativeai as genai




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


logger = logging.getLogger(__name__)
START_TIME = time.time()

class HealthView(views.APIView):
    def get(self, request, *args, **kwargs):
        uptime_seconds = int(time.time() - START_TIME)
        
        # 1. DB Probe
        db_reachable = "reachable"
        try:
            connection.ensure_connection()
        except (OperationalError, InterfaceError):
            db_reachable = "unreachable"
            
        # 2. LLM Probe
        llm_reachable = "reachable"
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        
        if not api_key or api_key in ["your_google_api_key_here", "dummy"]:
            llm_reachable = "missing_key"
        else:
            try:
                genai.configure(api_key=api_key)
                # Extremely lightweight ping using flash model
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content("ping", generation_config={"max_output_tokens": 1})
            except Exception:
                llm_reachable = "unreachable"
                
        # 3. Status Logic & Anti-Flood Logging
        components_healthy = 0
        if db_reachable == "reachable": components_healthy += 1
        if llm_reachable == "reachable": components_healthy += 1
        
        if components_healthy == 2:
            status_val = "Healthy"
            http_status = status.HTTP_200_OK
            logger.debug(f"Health check passed: status={status_val}, db={db_reachable}, llm={llm_reachable}")
        elif components_healthy == 1:
            status_val = "Degraded"
            http_status = status.HTTP_200_OK
            logger.warning(f"Health check degraded: status={status_val}, db={db_reachable}, llm={llm_reachable}")
        else:
            status_val = "Critical"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            logger.error(f"Health check critical: status={status_val}, db={db_reachable}, llm={llm_reachable}")
            
        return Response({
            "status": status_val,
            "uptime_seconds": uptime_seconds,
            "components": {
                "database": db_reachable,
                "llm": llm_reachable
            }
        }, status=http_status)
