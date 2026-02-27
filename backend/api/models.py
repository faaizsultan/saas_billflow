import uuid
from django.db import models

class Trace(models.Model):
    CATEGORY_CHOICES = [
        ('Billing', 'Billing'),
        ('Refund', 'Refund'),
        ('Account Access', 'Account Access'),
        ('Cancellation', 'Cancellation'),
        ('General Inquiry', 'General Inquiry'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_message = models.TextField()
    bot_response = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Trace'
        verbose_name_plural = 'Traces'

    def __str__(self):
        return f"Trace {self.id} - {self.category}"
