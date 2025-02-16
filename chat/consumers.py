# your_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message


# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        user = self.scope["user"]

        if user.is_anonymous:
            await self.close()
            return

        conversation = await self.get_conversation()
        if user not in conversation.participants.all():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data["content"]
        user = self.scope["user"]
        conversation = await self.get_conversation()

        # Create message with status "sent"
        message = await self.create_message(user, conversation, content)

        # Broadcast the message to the conversation group.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message.id,
                "sender_id": user.id,
                "content": content,
                "created_at": str(message.created_at),
                "status": message.status,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_conversation(self):
        return Conversation.objects.get(id=self.conversation_id)

    @database_sync_to_async
    def create_message(self, user, conversation, content):
        return Message.objects.create(conversation=conversation, sender=user, content=content)



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"notifications_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        # Send the notification event to the WebSocket.
        await self.send(text_data=json.dumps({"notification": event}))




































# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
#         self.room_group_name = f"chat_{self.conversation_id}"
#         user = self.scope["user"]

#         # Reject anonymous users.
#         if user.is_anonymous:
#             await self.close()
#             return

#         # Check if the user is a participant of the conversation.
#         conversation = await self.get_conversation()
#         if user not in conversation.participants.all():
#             await self.close()
#             return

#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         content = data["content"]

#         user = self.scope["user"]
#         conversation = await self.get_conversation()
#         message = await self.create_message(user, conversation, content)

#         # Broadcast chat message to the conversation group.
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat_message",
#                 "message_id": message.id,
#                 "sender_id": user.id,
#                 "content": content,
#                 "created_at": str(message.created_at),
#             },
#         )

#         # Send notifications to other participants.
#         participants = await self.get_participants(conversation)
#         for participant in participants:
#             if participant.id != user.id:
#                 await self.channel_layer.group_send(
#                     f"notifications_{participant.id}",
#                     {
#                         "type": "notification_message",
#                         "message_id": message.id,
#                         "conversation_id": self.conversation_id,
#                         "sender_id": user.id,
#                         "content": content,
#                         "created_at": str(message.created_at),
#                     },
#                 )

#     async def chat_message(self, event):
#         # Send the message event to the WebSocket.
#         await self.send(text_data=json.dumps(event))

#     @database_sync_to_async
#     def get_conversation(self):
#         return Conversation.objects.get(id=self.conversation_id)

#     @database_sync_to_async
#     def get_participants(self, conversation):
#         return list(conversation.participants.all())

#     @database_sync_to_async
#     def create_message(self, user, conversation, content):
#         return Message.objects.create(conversation=conversation, sender=user, content=content)