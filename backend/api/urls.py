from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TraceViewSet, AnalyticsView, ChatView

router = DefaultRouter()
router.register(r'traces', TraceViewSet, basename='trace')

urlpatterns = [
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('', include(router.urls)),
]
