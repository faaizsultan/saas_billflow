from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import Trace
from .llm_utils import generate_chat_response, classify_trace


class TraceModelTest(TestCase):
    def test_trace_creation(self):
        """Test that a Trace model can be created and auto_now_add works"""
        trace = Trace.objects.create(
            user_message="Hello",
            bot_response="Hi there!",
            category="General Inquiry",
            response_time_ms=150
        )
        self.assertEqual(Trace.objects.count(), 1)
        self.assertIsNotNone(trace.timestamp)


class LLMUtilsTest(TestCase):
    
    @patch('api.llm_utils.get_gemini_client', return_value=True)
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_generate_chat_response_success(self, mock_generate_content, mock_client):
        """Test successful chat response generation"""
        mock_response = MagicMock()
        mock_response.text = "This is a mocked response."
        mock_generate_content.return_value = mock_response
        
        response = generate_chat_response("test prompt")
        self.assertEqual(response, "This is a mocked response.")

    @patch('api.llm_utils.get_gemini_client', return_value=True)
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_generate_chat_response_failure(self, mock_generate_content, mock_client):
        """Test fallback when chat generation fails"""
        mock_generate_content.side_effect = Exception("API Timeout")
        
        response = generate_chat_response("test prompt")
        self.assertEqual(response, "Sorry, I am having trouble connecting to my brain right now. Please try again later.")

    @patch('api.llm_utils.get_gemini_client', return_value=True)
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_classify_trace_success(self, mock_generate_content, mock_client):
        """Test successful classification into a valid category"""
        mock_response = MagicMock()
        mock_response.text = "Billing"
        mock_generate_content.return_value = mock_response
        
        category = classify_trace("user: invoice", "bot: here is invoice")
        self.assertEqual(category, "Billing")

    @patch('api.llm_utils.get_gemini_client', return_value=True)
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_classify_trace_invalid_category(self, mock_generate_content, mock_client):
        """Test fallback when LLM returns an invalid category"""
        mock_response = MagicMock()
        mock_response.text = "Invalid Category"
        mock_generate_content.return_value = mock_response
        
        category = classify_trace("user: random", "bot: random")
        self.assertEqual(category, "General Inquiry")

    @patch('api.llm_utils.get_gemini_client', return_value=True)
    @patch('api.llm_utils.genai.GenerativeModel.generate_content')
    def test_classify_trace_failure(self, mock_generate_content, mock_client):
        """Test fallback when classification API call fails"""
        mock_generate_content.side_effect = Exception("API Error")
        
        category = classify_trace("user", "bot")
        self.assertEqual(category, "General Inquiry")


class TraceAPITest(APITestCase):

    def setUp(self):
        self.trace1 = Trace.objects.create(
            user_message="How do I get a refund?",
            bot_response="Here is the refund policy.",
            category="Refund",
            response_time_ms=200
        )
        self.trace2 = Trace.objects.create(
            user_message="Where is my bill?",
            bot_response="Here is your bill.",
            category="Billing",
            response_time_ms=100
        )

    def test_get_traces_all(self):
        """Test retrieving all traces"""
        url = reverse('trace-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_traces_filtered(self):
        """Test retrieving traces filtered by category"""
        url = reverse('trace-list')
        response = self.client.get(url, {'category': 'Refund'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'Refund')

    @patch('api.views.classify_trace')
    def test_create_trace_success(self, mock_classify):
        """Test successfully creating a trace via POST"""
        mock_classify.return_value = "Cancellation"
        
        url = reverse('trace-list')
        data = {'user_message': 'Cancel my account please', 'bot_response': 'Mocked API bot response.'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_message'], 'Cancel my account please')
        self.assertEqual(response.data['category'], 'Cancellation')
        self.assertEqual(response.data['bot_response'], 'Mocked API bot response.')
        self.assertTrue('response_time_ms' in response.data)
        self.assertEqual(Trace.objects.count(), 3)
        
    @patch('api.views.generate_chat_response')
    def test_chat_generation_success(self, mock_generate):
        """Test the new standalone chat endpoint"""
        mock_generate.return_value = "This is from the chat endpoint."
        
        url = reverse('chat')
        data = {'user_message': 'Hello bot'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bot_response'], "This is from the chat endpoint.")
        self.assertTrue('response_time_ms' in response.data)

    def test_create_trace_bad_request(self):
        """Test creating a trace without bot_response"""
        url = reverse('trace-list')
        data = {'user_message': 'hello'} # Missing bot_response
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AnalyticsAPITest(APITestCase):

    def test_analytics_empty_db(self):
        """Test analytics handle empty database without breaking (e.g. div by zero)"""
        url = reverse('analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_traces'], 0)
        self.assertEqual(response.data['average_response_time_ms'], 0)
        self.assertEqual(len(response.data['category_breakdown']), 0)

    def test_analytics_with_data(self):
        """Test analytics calculations with actual traces"""
        Trace.objects.create(user_message="1", bot_response="1", category="Billing", response_time_ms=100)
        Trace.objects.create(user_message="2", bot_response="2", category="Billing", response_time_ms=200)
        Trace.objects.create(user_message="3", bot_response="3", category="Refund", response_time_ms=300)
        
        url = reverse('analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_traces'], 3)
        self.assertEqual(response.data['average_response_time_ms'], 200) # (100+200+300)/3
        
        breakdown = response.data['category_breakdown']
        self.assertEqual(len(breakdown), 2)
        
        billing_stat = next(item for item in breakdown if item["category"] == "Billing")
        self.assertEqual(billing_stat['count'], 2)
        self.assertEqual(billing_stat['percentage'], 66.67) # 2/3 * 100
        
        refund_stat = next(item for item in breakdown if item["category"] == "Refund")
        self.assertEqual(refund_stat['count'], 1)
        self.assertEqual(refund_stat['percentage'], 33.33) # 1/3 * 100
