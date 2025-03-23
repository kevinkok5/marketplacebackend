from django.db import models
from django.contrib.auth import get_user_model
from store.models import Store
from store.models import Product
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# Create your models here.
class Conversation(models.Model):
    class Meta:
        ordering = ('-updated_at',)

    client = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="conversations")
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, related_name="store")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Conversation {self.id}"
    
    
class Message(models.Model):
    class Meta:
        ordering = ('-created_at',)


    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name="messages")
    sender_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)  # Determines if it's a User or Store
    sender_id = models.CharField(null=True, blank=True, max_length=200)  # Stores the actual ID of the sender
    sender = GenericForeignKey('sender_type', 'sender_id')  # Generic sender reference
    
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id} by {self.sender}"