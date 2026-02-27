from django.core.management.base import BaseCommand
from api.models import Trace
from django.utils import timezone
import datetime
import random

class Command(BaseCommand):
    help = 'Seeds the database with initial Trace data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing traces...')
        Trace.objects.all().delete()

        seed_data = [
            {
                "user_message": "Why was my card charged $49 this month?",
                "bot_response": "I see you're on the Pro plan which is $49/month. Your bill was generated on the 1st.",
                "category": "Billing"
            },
            {
                "user_message": "I want my money back, I never used the service.",
                "bot_response": "I understand. I have processed a full refund to your original payment method. Please allow 3-5 business days.",
                "category": "Refund"
            },
            {
                "user_message": "I forgot my password and can't log in.",
                "bot_response": "You can reset your password by clicking 'Forgot Password' on the login screen. I've also sent you a reset link via email.",
                "category": "Account Access"
            },
            {
                "user_message": "Please cancel my subscription immediately.",
                "bot_response": "I have canceled your subscription. You will have access until the end of your current billing cycle.",
                "category": "Cancellation"
            },
            {
                "user_message": "Does your platform support API rate limiting?",
                "bot_response": "Yes, our API supports rate limiting up to 1000 requests per minute on the enterprise plan.",
                "category": "General Inquiry"
            },
            {
                "user_message": "Where can I find the invoice for last month?",
                "bot_response": "You can download your invoices from the Billing section in your Account Dashboard.",
                "category": "Billing"
            },
            {
                "user_message": "I got charged twice this month.",
                "bot_response": "I apologize for the error. I've refunded the duplicate charge. It should appear in 3-5 days.",
                "category": "Refund"
            },
            {
                "user_message": "My two-factor authentication is not working.",
                "bot_response": "I've sent a temporary bypass code to your email. Please use it and then reset your 2FA settings.",
                "category": "Account Access"
            },
            {
                "user_message": "How do I delete my account permanently?",
                "bot_response": "You can delete your account from the Security tab in settings. Note that this action cannot be undone.",
                "category": "Cancellation"
            },
            {
                "user_message": "What integrations do you currently support?",
                "bot_response": "We currently integrate with Slack, Jira, GitHub, and major cloud providers.",
                "category": "General Inquiry"
            },
            {
                "user_message": "My payment failed but I have funds.",
                "bot_response": "Sometimes banks block transactions. Please contact your bank to authorize the charge from BillFlow.",
                "category": "Billing"
            },
            {
                "user_message": "Can I get a partial refund for the days I didn't use?",
                "bot_response": "Our policy doesn't typically allow prorated refunds, but I've made an exception and processed a $15 refund.",
                "category": "Refund"
            },
            {
                "user_message": "I'm not receiving the verification email.",
                "bot_response": "Please check your spam folder. I've also just triggered another verification email to you.",
                "category": "Account Access"
            },
            {
                "user_message": "I'm downgrading to the free tier.",
                "bot_response": "Your plan has been downgraded to the Free tier. The changes will take effect next billing period.",
                "category": "Cancellation"
            },
            {
                "user_message": "Is there a dark mode option?",
                "bot_response": "Yes! You can toggle dark mode in your Appearance settings.",
                "category": "General Inquiry"
            },
            {
                "user_message": "Update my credit card info.",
                "bot_response": "You can securely update your payment method in the Billing & Payment section of your profile.",
                "category": "Billing"
            },
            {
                "user_message": "The product lacks features, I want a refund.",
                "bot_response": "I'm sorry to hear that. Since you are within the 14-day window, I have processed a full refund.",
                "category": "Refund"
            },
            {
                "user_message": "How do I add team members?",
                "bot_response": "You can invite team members by going to Organization -> Members and clicking 'Invite'.",
                "category": "Account Access"
            },
            {
                "user_message": "Stop charging me.",
                "bot_response": "I've canceled your automatic renewal. You won't be charged again.",
                "category": "Cancellation"
            },
            {
                "user_message": "Do you have SOC2 compliance?",
                "bot_response": "Yes, we are SOC2 Type II compliant. You can request our report from the Trust Center.",
                "category": "General Inquiry"
            }
        ]

        now = timezone.now()
        traces_to_create = []

        for i, data in enumerate(seed_data):
            # stagger timestamps over the last 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            trace_time = now - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            response_time_ms = random.randint(300, 2500) # realistic LLM latencies

            trace = Trace(
                user_message=data["user_message"],
                bot_response=data["bot_response"],
                category=data["category"],
                response_time_ms=response_time_ms
            )
            # Need to set timestamp after creation because auto_now_add overrides initial value if not handled carefully.
            # However, bulk_create usually ignores auto_now_add if we explicitly provide it, but Django handles it weirdly on auto_now_add.
            # Actually, bulk_create works fine if we just assign the value, BUT for safety we modify save or do standard creation.
            # Standard creation is fast enough for 20 records.
            trace.save()
            # override timestamp which was forced to now() by auto_now_add
            Trace.objects.filter(id=trace.id).update(timestamp=trace_time)
            
            self.stdout.write(f"Created trace: {data['category']}")

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(seed_data)} traces.'))
