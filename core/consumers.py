import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatSession, Message, UserChatSession, CustomUser
from asgiref.sync import sync_to_async
from django.conf import settings
from django.apps import apps
from django.shortcuts import get_object_or_404

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Update unread count when chat is opened
        user = self.scope['user']
        await self.update_unread_count(self.session_id, user)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def update_unread_count(self, session_id, user):
        session = await self.get_chat_session(session_id)
        user_chat_session = await self.get_user_chat_session(user, session)
        await user_chat_session.update_unread_count()

    @sync_to_async
    def get_chat_session(self, session_id):
        session = ChatSession.objects.get(id=session_id)
        return session

    @sync_to_async
    def get_or_create_user_chat_session(self, user, chat_session):
        return UserChatSession.objects.get_or_create(user=user, chat_session=chat_session)

    @sync_to_async
    def get_unread_count(self, session, user):
        user_chat_session = UserChatSession.objects.get(user=user, chat_session=session)
        user_chat_session.update_unread_count()
        return user_chat_session.unread_messages_count

    @sync_to_async
    def get_session_user(self, session):
        return session.user
    
    @sync_to_async
    def get_session_consultant(self, session):
        return session.consultant

    @sync_to_async
    def get_user_chat_session(self, user, chat_session):
        return UserChatSession.objects.get(user=user, chat_session=chat_session)

    @sync_to_async
    def get_user_chat_session_user(self, user_chat_session):
        return user_chat_session.user
    
    @sync_to_async
    def get_user(self, user_id):
        user = CustomUser.objects.get(id=user_id)
        return user

    @sync_to_async
    def get_recipient(self, session, sender_id):
        if session.user.id == int(sender_id):
            return session.consultant
        else:
            return session.user
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        session_id = data.get('session_id')
        sender_id = data.get('sender')
        message = data.get('message')
        print(f"the data  is {data}")

        session = await self.get_chat_session(self.session_id)
        message_obj = await self.save_message(sender_id, message)

        user = await self.get_user(sender_id)
        user_chat_session, _ = await self.get_or_create_user_chat_session(user, session)

        if user == await self.get_session_user(session):
            recipient = await self.get_session_consultant(session)
        else:
            recipient = await self.get_session_user(session)

        unread_count = await self.get_unread_count(session, recipient)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_id,
                'unread_count': unread_count,
            }
        )
        await self.update_unread_count(session_id, recipient)

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        session_id = self.session_id

        session = await self.get_chat_session(self.session_id)
        user_id = self.scope['user'].id
        user = await self.get_user(user_id)
        recipient = await self.get_recipient(session, sender)
        unread_count = await self.get_unread_count(session, recipient)

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'session_id': session_id,
            'unread_count': unread_count,
        }))

        await self.update_unread_count(session_id, recipient)

    async def save_message(self, sender_id, content):
        session = await sync_to_async(get_object_or_404)(ChatSession, id=self.session_id)
        User = apps.get_model(settings.AUTH_USER_MODEL)
        sender = await User.objects.aget(id=sender_id)
        
        message = await Message.objects.acreate(session=session, sender=sender, content=content)

        session_user = await self.get_session_user(session)
        if sender == session_user:
            recipient = await self.get_session_consultant(session)
        else:
            recipient = session.user

        user_chat_session = await self.get_user_chat_session(recipient, session)
        await self.update_unread_count(self.session_id, recipient)

        return message

    @sync_to_async
    def mark_messages_as_read(self, session, user):
        unread_messages = session.messages.exclude(read_by=user)
        for message in unread_messages:
            message.read_by.add(user)

        user_chat_session = UserChatSession.objects.get(user=user, chat_session=session)
        user_chat_session.update_unread_count()
