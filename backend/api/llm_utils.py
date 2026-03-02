import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


CHATBOT_SYSTEM_PROMPT = getattr(settings, 'CHATBOT_SYSTEM_PROMPT', "You are a customer support agent.")
CLASSIFICATION_PROMPT = getattr(settings, 'CLASSIFICATION_PROMPT', "Classify the user message into a category.")



def get_gemini_client():
    """Initializes the Gemini client if the API key is present."""
    api_key = getattr(settings, 'GOOGLE_API_KEY', None)
    if api_key and api_key != "your_google_api_key_here":
        genai.configure(api_key=api_key)
        return True
    return False

def generate_chat_response(prompt: str) -> str:
    """Generates a chatbot response using Gemini."""
    if not get_gemini_client():
        logger.warning("GOOGLE_API_KEY not set or invalid. Returning fallback response.")
        return "I am currently unable to answer that. Please contact support at support@billflow.com."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=CHATBOT_SYSTEM_PROMPT)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error calling Gemini for chat response: {str(e)}")
        return "Sorry, I am having trouble connecting to my brain right now. Please try again later."


def classify_trace(user_message: str, bot_response: str) -> str:
    """Classifies a conversation into a predefined category using Gemini."""
    fallback_category = "General Inquiry"
    
    if not get_gemini_client():
        logger.warning("GOOGLE_API_KEY not set or invalid. Returning fallback category.")
        return fallback_category

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = CLASSIFICATION_PROMPT.format(
            user_message=user_message, 
            bot_response=bot_response
        )
        response = model.generate_content(prompt)
        category = response.text.strip()
        
        valid_categories = ["Billing", "Refund", "Account Access", "Cancellation", "General Inquiry"]
        
        # Clean up any potential markdown or extra spaces the LLM might have hallucinated
        cleaned_category = category.replace("`", "").strip()
        
        if cleaned_category in valid_categories:
            return cleaned_category
        else:
            logger.warning(f"Unrecognized category returned by LLM: {cleaned_category}")
            return fallback_category
            
    except Exception as e:
        logger.error(f"Error calling Gemini for classification: {str(e)}")
        return fallback_category
