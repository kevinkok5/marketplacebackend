# your_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message
from graphene.relay import Node
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.text import slugify
from .schema.types import ConversationType, MessageType
from users.schema import MeType
from django.conf import settings
from asgiref.sync import sync_to_async
from store.schema.types import ProductMediasType
from django.utils import timezone
from django.contrib.auth import get_user_model

domain = settings.SITE_URL  # Ensure you have this set in settings.py

from store.models import Product, Store, Media
from store.schema.types import StoreType

class ChatConsumer(AsyncWebsocketConsumer):
    # this consumer is not secure and other users that are neither the conversatoin client nor the conversation store
    # can still send messages, to fix this I should find a way to check if the user of the store trying to access this is part of the conversation or 
    # authorized to take part to this conversation
    async def connect(self):

        self.conversation_id = self.scope["url_route"]["kwargs"]["chat_id"]
        safe_conversation_id = slugify(self.conversation_id)

        self.room_group_name = f"chat_{safe_conversation_id}"
        user = self.scope["user"]

        if user is None or user.is_anonymous:
            await self.send(json.dumps({"error": "Authentication failed"}))
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept('jwt')
        # Note: If you want to await sending, use "await self.send(...)" here.
        await self.send(json.dumps({
            'type': 'connection_established', 
            'message': 'You are now connected'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("received data: ", data)

    #     # Check if this is the authentication message
    #     if data.get("type") == "auth":
    #         token = data.get("token")
    #         user = await self.authenticate_user(token)
    #         
    #         # Store the authenticated user in the connection's scope
    #         self.scope["user"] = user
    #         await self.send(json.dumps({"message": "Authentication successful"}))
    #         return

        try: 
            content = data["content"]
            forAId = data["forAId"]
            user = self.scope["user"]
        except KeyError as e:
            await self.send(json.dumps({"error": f"KeyError: Missing key '{e.args[0]}'"}))
            return

        # if user is None or user.is_anonymous:
        #     await self.send(json.dumps({"error": "Authentication failed"}))
        #     await self.close()
        #     return
        print("work fine up until here")

        conversation = await self.get_conversation()
        if not conversation:
            await self.send(json.dumps({"error": "Couldn't Find the chat"}))
            return

        # this should have been from who not for who as it return the object (user or store) from which the message was sent
        for_object, for_object_type_name = await self.get_for_who_object(forAId, user, conversation) 
        if not for_object:
            await self.send(json.dumps({"error": "Couldn't identify whose the chat"}))
            return 

        # Create message with status "sent"
        message = await self.create_message(for_object, conversation, content)
        if not message: 
            await self.send(json.dumps({"error": "Couldn't create the message"}))
            return 

        try:
            # Use our helper to generate global IDs in a sync thread.
            message_global_id = await self.generate_global_id(MessageType._meta.name, message.id)
            sender_global_id = await self.generate_global_id(for_object_type_name, for_object.id)
        except Exception as e:
            await self.send(json.dumps({"error": f"Error generating global ID: {str(e)}"}))
            return

        # Manually update the updated_at field
        conversation.updated_at = timezone.now()
        await sync_to_async(conversation.save, thread_sensitive=True)(update_fields=['updated_at'])

        # Broadcast the message to the conversation group.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": message_global_id,
                "senderId": sender_global_id,
                "content": content,
                "createdAt": str(message.created_at),
                "status": message.status,
            },
        )

        # Also send it to the store-level group to notify StartConversationConsumer
        try:
            conversation_global_id = await self.generate_global_id(ConversationType._meta.name, conversation.id)
            store_global_id = await self.generate_global_id(StoreType._meta.name, conversation.store.id)
            client_global_id = await self.generate_global_id(MeType._meta.name, conversation.client.id)
        except Exception as e:
            await self.send(json.dumps({"error": f"Error creating or generating a global ID: {str(e)}"}))
            return

        

        safe_store_id = slugify(store_global_id)
        store_group_name = f"chat_{safe_store_id}"

        await self.channel_layer.group_send(
            store_group_name,
            {
                "type": "chat_message",
                "id": conversation_global_id,
                "messages": {
                    "edges": [{
                        "node": {
                            "type": "chat_message",
                            "id": message_global_id,
                            "senderId": sender_global_id,
                            "content": content,
                            "createdAt": str(message.created_at),
                            "status": message.status,
                        },
                    }]
                },
                "updatedAt": str(conversation.updated_at),
            },
        )

        safe_client_id= slugify(client_global_id)
        client_group_name = f"chat_{safe_client_id}"

        await self.channel_layer.group_send(
            client_group_name,
            {
                "type": "chat_message",
                "id": conversation_global_id,
                "messages": {
                    "edges": [{
                        "node": {
                            "type": "chat_message",
                            "id": message_global_id,
                            "senderId": sender_global_id,
                            "content": content,
                            "createdAt": str(message.created_at),
                            "status": message.status,
                        },
                    }]
                },
                "updatedAt": str(conversation.updated_at),
            },
        )
        
        notification_group_name = None

        # notify the receiver of a new message
        if for_object_type_name == 'MeType':
            notification_group_name = f"notifications_{safe_store_id}"
        elif for_object_type_name == 'StoreType':
            notification_group_name = f"notifications_{safe_client_id}"

        count = 0
        # for message in conversation.messages:
        #     if message.sender_id == for_object.id and  message.status in ["sent", "delivered"]:
        #         count = count + 1

        if notification_group_name:
            await self.channel_layer.group_send(
                client_group_name,
                {
                    "type": "chat_notification_message",
                    "totalUnread":  count
                },
            )

            # Message.objects.filter(
            #             conversation__client=user
            #         ).exclude(sender=user).filter(status__in=["sent", "delivered"]).count()


    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(token)
            return auth.get_user(validated_token)
        except Exception as e:
            print(f"JWT Authentication failed: {e}")
            return None

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_conversation(self):
        try:
            type_name, db_id = Node.resolve_global_id(self, self.conversation_id)

            # Use select_related to prefetch 'store' and 'client'
            return Conversation.objects.select_related('store', 'client').get(id=db_id)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, for_object, conversation, content):
        try:
            return Message.objects.create(
                conversation=conversation,
                sender_type=ContentType.objects.get_for_model(for_object),
                sender_id=for_object.id,
                content=content
            )
        except Exception as e:
            print(f"Error creating message: {e}")
            return None

    @database_sync_to_async
    def get_for_who_object(self, forAid, scopeUser, conversation):
        try:
            type_name, db_id = Node.resolve_global_id(self, forAid)
        except (ValueError, Store.DoesNotExist):
            return [None, None]
        
        if type_name == "MeType": 
            try:
                user = get_user_model().objects.get(id=db_id)
                if not user == scopeUser or not user == conversation.client:
                    return [None, None]
                return [user, type_name]
            except get_user_model().DoesNotExist:
                return [None, None]
        else:
            try:
                store = Store.objects.get(id=db_id)
                if not scopeUser == store.owner and not store == conversation.store:
                    return [None, None]
                return [store, type_name]
            except Store.DoesNotExist:
                return [None, None]

    @database_sync_to_async
    def generate_global_id(self, type_name, object_id):
        # This method is now a proper instance method wrapped for sync calls.
        return Node.to_global_id(type_name, object_id)



class StartCoversationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.store_or_user_id = self.scope["url_route"]["kwargs"]["store_or_user_id"]
        safe_store_or_user_id = slugify(self.store_or_user_id)
        self.room_group_name = f"chat_{safe_store_or_user_id}"

        user = self.scope["user"]

        if user is None or user.is_anonymous:
            await self.send(json.dumps({"error": "Authentication failed"}))
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept('jwt')

        await self.send(json.dumps({'type': 'connection_established', 'message': 'You are now connected'}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # # Check if this is the authentication message
        # if data.get("type") == "auth":
        #     token = data.get("token")
        #     user = await self.authenticate_user(token)
        #     if user is None or user.is_anonymous:
        #         await self.send(json.dumps({"error": "Authentication failed"}))
        #         await self.close()
        #         return
        #     # Store the authenticated user in the connection's scope
        #     self.scope["user"] = user
        #     await self.send(json.dumps({"message": "Authentication successful"}))
        #     return
        
        try: 
            content = data["content"]
            product_id = data["productId"]
            user = self.scope["user"]
        except KeyError as e:
            await self.send(json.dumps({"error": f"KeyError: Missing key '{e.args[0]}'"}))
            return

        # if user is None or user.is_anonymous:
        #     await self.send(json.dumps({"error": "Authentication failed"}))
        #     await self.close()
        #     return
        

        store = await self.get_store()
        product, product_type_name = await self.get_product(product_id)

        if not store:
            await self.send(json.dumps({"error": "Store not found"}))
            return 
        if not product: 
            await self.send(json.dumps({"error": "Product not found"}))
            return 

        product_media = await sync_to_async(Media.objects.filter(product=product).first, thread_sensitive=True)()
        product_media_global_id = Node.to_global_id(ProductMediasType._meta.name, product_media.id)
        
        product_media_object = {
            "edges": [
                {
                    "node": {
                        "id": product_media_global_id,
                        "media": f"{domain}{product_media.media.url}" if product_media.media.url else None
                    }
                }
            ]
        }

        if product_type_name == "ItemType":
            productObj = {
                "id": product_id,
                "name": product.name, 
                "medias": product_media_object,
                "productType": product.product_type
            }
        elif product_type_name == "VehicleType":
            productObj = {
                "id": product_id,
                "make": product.make, 
                "model": product.model,
                "year": product.year,
                "medias": product_media_object,
                "productType": product.product_type

            }
        elif product_type_name == "HouseType":
            productObj = {
                "id": product_id,
                "description": product.description, 
                "medias": product_media_object,
                "productType": product.product_type
            }

        # We first create the conversation
        conversation, created = await self.get_or_create_conversation(user, store, product)
        if not created:
            # Manually update the updated_at field
            conversation.updated_at = timezone.now()

            # Save only the updated_at field to avoid unnecessary writes
            await sync_to_async(conversation.save, thread_sensitive=True)(update_fields=['updated_at'])
            print("Conversation created")
        # then we create a message with the status set "sent"
        message = await self.create_message(user, conversation, content)

        try:
            conversation_global_id = Node.to_global_id(ConversationType._meta.name, conversation.id)
            message_global_id = Node.to_global_id(MessageType._meta.name, message.id)
            user_global_id = Node.to_global_id(MeType._meta.name, user.id)
            # product_global_id = Node.to_global_id(product_type_name, product.id)
        except Exception as e:
            await self.send(json.dumps({"error": f"Error generating global ID: {str(e)}"}))
            return

        # print("Conversation id: " + conversation_global_id + ", user id: " + user_global_id + ", message id: " + message_global_id)

        # Broadcast the message to the conversation group.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": conversation_global_id,
                "client": {
                    "id": user_global_id,
                    "username": user.username,
                    "firstName": user.first_name,
                },
                "store": {
                    "id": self.store_or_user_id,
                    "name": store.name,
                    "profileImage": f"{domain}{store.profile_image.url}" if store.profile_image else None
                },
                "product": productObj,
                "messages": {
                    "edges": [{
                        "node": {
                            "content": content,
                            "id": message_global_id,
                            "senderId": user_global_id,
                            "createdAt": str(message.created_at),
                            "status": message.status,
                        }
                    }]
                },
                "updatedAt": str(conversation.updated_at),
            },
        )

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            auth = JWTAuthentication() 
            validated_token = auth.get_validated_token(token)
            return auth.get_user(validated_token)
        except Exception as e:
            print(f"JWT Authentication failed: {e}")
            return None
        
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_store(self):
        try:
            type_name, db_id = Node.resolve_global_id(self, self.store_or_user_id)
            return Store.objects.get(id=db_id)
        except (ValueError, Store.DoesNotExist):
            return None  # Handle this case in `receive()`
    
    @database_sync_to_async
    def get_product(self, product_id):
        try:
            type_name, db_id = Node.resolve_global_id(self, product_id)
            return [Product.objects.get(id=db_id), type_name]
        except (ValueError, Store.DoesNotExist):
            return [None, None]  # Handle this case in `receive()`
        
    @database_sync_to_async
    def get_or_create_conversation(self, user, store, product):
        return Conversation.objects.get_or_create(client=user, store=store, product=product)
    
    @database_sync_to_async
    def create_message(self, user, conversation, content):
        try:

            return Message.objects.create(
                conversation=conversation,
                sender_type=ContentType.objects.get_for_model(user),
                sender_id=user.id,
                content=content
            )
        except Exception as e:
            print(f"Error creating message: {e}")
            return None  # Return None if message creation fails
        



class ChatNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.store_or_user_id = self.scope["url_route"]["kwargs"]["store_or_user_id"]

        safe_store_or_user_id = slugify(self.store_or_user_id)
        self.room_group_name = f"chat_notification_{safe_store_or_user_id}"

        user = self.scope["user"]

        if user is None or user.is_anonymous:
            await self.send(json.dumps({"error": "Authentication failed"}))
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        self.send(text_data=json.dumps({'type': 'connection_established', 'message': 'You are now connected'}))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        # Send the notification event to the WebSocket.
        await self.send(text_data=json.dumps(event))


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