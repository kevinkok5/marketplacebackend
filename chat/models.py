from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
class Conversation(models.Model):
    participants = models.ManyToManyField(get_user_model(), related_name="conversations")
    product = models.ForeignKey('Product', null=True, blank=True, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"
    
class Message(models.Model):
    STATUS_CHOICES = [
         ('sent', 'Sent'),
         ('delivered', 'Delivered'),
         ('read', 'Read'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id}"