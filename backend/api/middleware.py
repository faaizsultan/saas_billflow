import time
import logging

logger = logging.getLogger('api.requests')

class StructuredLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Skip structured logging for the noisy /health endpoint
        if request.path == '/health':
            return response
            
        # Get client IP properly, handling proxies if they exist
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        request_meta = {
            "path": request.path,
            "method": request.method,
            "status": response.status_code,
            "ip": ip,
            "duration_ms": duration_ms
        }
        
        # Add correlation ID (Trace ID) if this was a trace creation
        if request.path == '/api/traces/' and request.method == 'POST' and response.status_code == 201:
            try:
                import json
                if hasattr(response, 'content'):
                    response_data = json.loads(response.content.decode('utf-8'))
                    if 'id' in response_data:
                        request_meta['trace_id'] = response_data['id']
            except Exception:
                pass # Don't crash logging if parsing fails
        
        if response.status_code >= 500:
            logger.error("HTTP Request Failed", extra={"request_meta": request_meta})
        elif response.status_code >= 400:
            logger.warning("HTTP Request Client Error", extra={"request_meta": request_meta})
        else:
            logger.info("HTTP Request Completed", extra={"request_meta": request_meta})

        return response
