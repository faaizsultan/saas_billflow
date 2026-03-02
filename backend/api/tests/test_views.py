from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from api.models import Trace

class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @override_settings(GOOGLE_API_KEY='valid_key_123')
    @patch('api.views.genai.GenerativeModel')
    def test_health_all_systems_go(self, mock_model):
        # Mock genai so it doesn't make network calls
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        
        response = self.client.get('/health')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['status'], 'Healthy')
        self.assertEqual(data['components']['database'], 'reachable')
        self.assertEqual(data['components']['llm'], 'reachable')
        self.assertTrue('uptime_seconds' in data)

    @override_settings(GOOGLE_API_KEY=None)
    def test_health_missing_llm_key(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Ensure it still returns 200
        
        data = response.json()
        self.assertEqual(data['status'], 'Degraded')
        self.assertEqual(data['components']['llm'], 'missing_key')

    @override_settings(GOOGLE_API_KEY=None)
    @patch('api.views.connection.ensure_connection')
    def test_health_db_down_and_llm_missing_critical(self, mock_ensure_connection):
        from django.db import OperationalError
        mock_ensure_connection.side_effect = OperationalError("DB connection failed")
        
        response = self.client.get('/health')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        data = response.json()
        self.assertEqual(data['status'], 'Critical')
        self.assertEqual(data['components']['database'], 'unreachable')


class TraceEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @override_settings(GOOGLE_API_KEY='valid_key_123')
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_successful_trace_creation(self, mock_generate):
        # Set up fake responses
        bot_response = MagicMock()
        bot_response.text = "Certainly, I have refunded your purchase."
        
        classification_response = MagicMock()
        classification_response.text = "Refund"
        
        # It's called twice: 1 for chat response, 1 for classification
        mock_generate.side_effect = [bot_response, classification_response]
        
        response = self.client.post('/api/traces/', {"user_message": "I want a refund please."})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['category'], "Refund")
        self.assertEqual(data['bot_response'], bot_response.text)

    @override_settings(GOOGLE_API_KEY='valid_key_123')
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_trace_creation_llm_hallucination(self, mock_generate):
        # Set up fake responses where classification is garbage
        bot_response = MagicMock()
        bot_response.text = "Potato"
        
        classification_response = MagicMock()
        classification_response.text = "Potato Category"
        
        mock_generate.side_effect = [bot_response, classification_response]
        
        response = self.client.post('/api/traces/', {"user_message": "Tell me about potatoes."})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        # Should fallback to General Inquiry when classification doesn't match predefined categories
        self.assertEqual(data['category'], "General Inquiry")

    @override_settings(GOOGLE_API_KEY=None)
    def test_trace_creation_missing_key(self):
        # With missing key, it should fallback without calling SDK
        response = self.client.post('/api/traces/', {"user_message": "Hello"})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['category'], "General Inquiry")
        self.assertEqual(data['bot_response'], "I cannot chat right now (LLM API Key missing). Please contact support at help@supportlens.com")

class AnalyticsEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Seed test data
        Trace.objects.create(user_message="Msg1", bot_response="R1", category="Refund", response_time_ms=10)
        Trace.objects.create(user_message="Msg2", bot_response="R2", category="Refund", response_time_ms=10)
        Trace.objects.create(user_message="Msg3", bot_response="R3", category="Cancellation", response_time_ms=10)
        Trace.objects.create(user_message="Msg4", bot_response="R4", category="General Inquiry", response_time_ms=10)

    def test_analytics_aggregations(self):
        response = self.client.get('/api/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total_traces'], 4)
        
        # Verify Refund math
        refund_stats = next(item for item in data['category_breakdown'] if item['category'] == 'Refund')
        self.assertEqual(refund_stats['count'], 2)
        # 2 out of 4 is 50.0%
        self.assertEqual(float(refund_stats['percentage']), 50.0)

        # Verify Cancellation math
        cancel_stats = next(item for item in data['category_breakdown'] if item['category'] == 'Cancellation')
        self.assertEqual(cancel_stats['count'], 1)
        self.assertEqual(float(cancel_stats['percentage']), 25.0)
