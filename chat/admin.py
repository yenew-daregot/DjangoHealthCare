from django.contrib import admin
from .models import ChatRoom, Message, ChatParticipant, ChatNotification

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['timestamp', 'is_read']
    can_delete = False

class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 0
    readonly_fields = ['joined_at', 'last_read']

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'room_type', 'is_active', 'created_at', 'last_activity']
    list_filter = ['room_type', 'is_active', 'created_at']
    search_fields = ['patient__user__username', 'doctor__user__username', 'title']
    readonly_fields = ['created_at', 'last_activity']
    inlines = [ChatParticipantInline, MessageInline]
    date_hierarchy = 'created_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat_room', 'sender', 'message_type', 'is_read', 'timestamp']
    list_filter = ['message_type', 'is_read', 'timestamp']
    search_fields = ['chat_room__patient__user__username', 'chat_room__doctor__user__username', 'content']
    readonly_fields = ['timestamp', 'read_at']
    date_hierarchy = 'timestamp'

@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ['chat_room', 'user', 'joined_at', 'last_read', 'is_online']
    list_filter = ['is_online', 'joined_at']
    search_fields = ['chat_room__title', 'user__username']
    readonly_fields = ['joined_at', 'last_read']

@admin.register(ChatNotification)
class ChatNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'chat_room', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'chat_room__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'