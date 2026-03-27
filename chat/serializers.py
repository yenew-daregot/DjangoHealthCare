from rest_framework import serializers
from .models import ChatRoom, Message, ChatParticipant, ChatNotification
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer
from users.serializers import UserSerializer
from prescriptions.serializers import PrescriptionSerializer
from labs.serializers import LabRequestSerializer
from appointments.serializers import AppointmentSerializer

class ChatParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'user_id', 'chat_room', 'role', 'joined_at', 'last_read', 'is_online', 'is_active']
        read_only_fields = ['joined_at', 'last_read']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    chat_room_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat_room', 'chat_room_id', 'sender', 'sender_name', 'message_type', 
            'content', 'file', 'file_name', 'file_size', 'timestamp', 'read_at', 
            'is_read', 'related_prescription', 'related_lab_result', 'related_appointment'
        ]
        read_only_fields = ['timestamp', 'read_at', 'file_name', 'file_size', 'sender']

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['chat_room', 'message_type', 'content', 'file']
    
    def validate(self, data):
        # Ensure user has access to the chat room
        user = self.context['request'].user
        chat_room = data.get('chat_room')
        
        if chat_room and not ChatParticipant.objects.filter(
            chat_room=chat_room, user=user, is_active=True
        ).exists():
            raise serializers.ValidationError("You don't have access to this chat room.")
        
        return data

class ChatRoomSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participants = ChatParticipantSerializer(many=True, read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'patient', 'patient_id', 'doctor', 'doctor_id', 'room_type', 
            'title', 'created_at', 'last_activity', 'is_active', 'last_message', 
            'unread_count', 'participants'
        ]
        read_only_fields = ['created_at', 'last_activity', 'title']
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

class ChatRoomDetailSerializer(ChatRoomSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ChatRoomSerializer.Meta):
        fields = ChatRoomSerializer.Meta.fields + ['messages']

class ChatNotificationSerializer(serializers.ModelSerializer):
    chat_room = ChatRoomSerializer(read_only=True)
    message = MessageSerializer(read_only=True)
    
    class Meta:
        model = ChatNotification
        fields = [
            'id', 'chat_room', 'user', 'message', 
            'notification_type', 'is_read', 'created_at'
        ]
        read_only_fields = ['created_at']


class FileUploadSerializer(serializers.Serializer):
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    file = serializers.FileField()
    
    def validate(self, data):
        user = self.context['request'].user
        chat_room = data['chat_room']
        
        # Check if user is a participant in the chat room
        if not ChatParticipant.objects.filter(chat_room=chat_room, user=user).exists():
            raise serializers.ValidationError("You don't have access to this chat room.")
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if data['file'].size > max_size:
            raise serializers.ValidationError("File size must be less than 10MB.")
        
        # Validate file types
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if data['file'].content_type not in allowed_types:
            raise serializers.ValidationError("File type not allowed.")
        
        return data

class CreateChatRoomSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()
    
    class Meta:
        model = ChatRoom
        fields = ['patient_id', 'doctor_id', 'room_type', 'title']
    
    def validate(self, data):
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        
        # Check if chat room already exists
        if ChatRoom.objects.filter(
            patient_id=patient_id,
            doctor_id=doctor_id,
            room_type=data.get('room_type', 'consultation'),
            is_active=True
        ).exists():
            raise serializers.ValidationError("Chat room already exists.")
        
        return data

class MarkMessagesReadSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    room_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        if not data.get('message_ids') and not data.get('room_id'):
            raise serializers.ValidationError(
                "Either message_ids or room_id must be provided."
            )
        return data