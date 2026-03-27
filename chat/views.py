from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from .models import ChatRoom, Message, ChatParticipant, ChatNotification
from .serializers import (
    ChatRoomSerializer, ChatRoomDetailSerializer, MessageSerializer,
    MessageCreateSerializer, ChatParticipantSerializer, ChatNotificationSerializer,
    FileUploadSerializer
)

# Chat Room Views
class ChatRoomListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return ChatRoom.objects.filter(patient__user=user, is_active=True)
        elif user.user_type == 'doctor':
            return ChatRoom.objects.filter(doctor__user=user, is_active=True)
        else:
            return ChatRoom.objects.none()

    def perform_create(self, serializer):
        chat_room = serializer.save()
        # Create participants
        ChatParticipant.objects.create(chat_room=chat_room, user=chat_room.patient.user)
        ChatParticipant.objects.create(chat_room=chat_room, user=chat_room.doctor.user)

class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatRoomDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            Q(patient__user=user) | Q(doctor__user=user)
        )

class PatientChatRoomsView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return ChatRoom.objects.filter(patient_id=patient_id, is_active=True)

class DoctorChatRoomsView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.kwargs['doctor_id']
        
        # Add debugging
        print(f"DoctorChatRoomsView: doctor_id={doctor_id}, user={self.request.user}")
        
        try:
            # Verify the doctor exists
            from doctors.models import Doctor
            doctor = Doctor.objects.get(id=doctor_id)
            print(f"Doctor found: {doctor}")
            
            # Get chat rooms for this doctor
            queryset = ChatRoom.objects.filter(doctor_id=doctor_id, is_active=True)
            print(f"Chat rooms found: {queryset.count()}")
            
            return queryset
            
        except Doctor.DoesNotExist:
            print(f"Doctor with ID {doctor_id} not found")
            return ChatRoom.objects.none()
        except Exception as e:
            print(f"Error in DoctorChatRoomsView: {e}")
            return ChatRoom.objects.none()

class FindOrCreateChatRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        patient_id = request.data.get('patient_id')
        doctor_id = request.data.get('doctor_id')
        room_type = request.data.get('room_type', 'consultation')

        if not patient_id or not doctor_id:
            return Response(
                {'error': 'Both patient_id and doctor_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that patient and doctor exist
        from patients.models import Patient
        from doctors.models import Doctor
        
        try:
            patient = Patient.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=doctor_id)
        except (Patient.DoesNotExist, Doctor.DoesNotExist):
            return Response(
                {'error': 'Patient or Doctor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Try to find existing active chat room
        chat_room = ChatRoom.objects.filter(
            patient_id=patient_id,
            doctor_id=doctor_id,
            room_type=room_type,
            is_active=True
        ).first()

        if not chat_room:
            # Create new chat room
            chat_room = ChatRoom.objects.create(
                patient_id=patient_id,
                doctor_id=doctor_id,
                room_type=room_type
            )
            # Create participants with proper roles
            ChatParticipant.objects.create(
                chat_room=chat_room, 
                user=patient.user,
                role='patient'
            )
            ChatParticipant.objects.create(
                chat_room=chat_room, 
                user=doctor.user,
                role='doctor'
            )

        serializer = ChatRoomDetailSerializer(chat_room)
        return Response(serializer.data)

# Message Views
class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(chat_room__participants__user=user)

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        
        # Update chat room last activity
        message.chat_room.last_activity = timezone.now()
        message.chat_room.save()
        
        # Create notifications for other participants
        self.create_notifications(message)

    def create_notifications(self, message):
        participants = message.chat_room.participants.exclude(user=message.sender)
        for participant in participants:
            ChatNotification.objects.create(
                user=participant.user,
                chat_room=message.chat_room,
                notification_type='new_message',
                message=message
            )

class MessageDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(chat_room__participants__user=user)

class RoomMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        user = self.request.user
        
        # Verify user has access to this room
        if not ChatRoom.objects.filter(
            id=room_id, 
            participants__user=user
        ).exists():
            return Message.objects.none()
        
        return Message.objects.filter(chat_room_id=room_id)

class MarkMessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        
        # Verify user has access to this message
        if not message.chat_room.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.mark_as_read()
        return Response({'status': 'message marked as read'})

class MarkAllMessagesReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        user = request.user
        
        # Verify user has access to this room
        if not ChatRoom.objects.filter(
            id=room_id, 
            participants__user=user
        ).exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark all unread messages in the room as read
        unread_messages = Message.objects.filter(
            chat_room_id=room_id,
            is_read=False
        ).exclude(sender=user)
        
        for message in unread_messages:
            message.mark_as_read()
        
        return Response({
            'status': 'all messages marked as read',
            'updated_count': unread_messages.count()
        })

# File Upload View
class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            
            # Create a message with the file
            message = Message.objects.create(
                chat_room=serializer.validated_data['chat_room'],
                sender=request.user,
                message_type='file',
                file=file,
                file_name=file.name,
                file_size=file.size
            )
            
            # Update chat room activity
            message.chat_room.last_activity = timezone.now()
            message.chat_room.save()
            
            # Create notifications
            self.create_file_notifications(message)
            
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_file_notifications(self, message):
        participants = message.chat_room.participants.exclude(user=message.sender)
        for participant in participants:
            ChatNotification.objects.create(
                user=participant.user,
                chat_room=message.chat_room,
                notification_type='file_shared',
                message=message
            )

# Participant Views
class RoomParticipantsView(generics.ListAPIView):
    serializer_class = ChatParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        return ChatParticipant.objects.filter(chat_room_id=room_id)

class ParticipantDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ChatParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatParticipant.objects.filter(user=user)

# Notification Views
class ChatNotificationListView(generics.ListAPIView):
    serializer_class = ChatNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatNotification.objects.filter(user=self.request.user, is_read=False)

class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(ChatNotification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

class MarkAllNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated_count = ChatNotification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'status': 'all notifications marked as read',
            'updated_count': updated_count
        })

# WebSocket Support
class WebSocketTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Generate JWT token for WebSocket authentication
        payload = {
            'user_id': request.user.id,
            'username': request.user.username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response({'token': token})

# Test endpoint for debugging
class ChatTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user info
        user_info = {
            'id': user.id,
            'username': user.username,
            'user_type': getattr(user, 'user_type', 'unknown'),
            'is_authenticated': user.is_authenticated,
        }
        
        # Check if user is a doctor
        doctor_info = None
        if hasattr(user, 'user_type') and user.user_type == 'DOCTOR':
            try:
                from doctors.models import Doctor
                doctor = Doctor.objects.get(user=user)
                doctor_info = {
                    'id': doctor.id,
                    'specialization': str(doctor.specialization),
                    'is_available': doctor.is_available,
                    'is_verified': doctor.is_verified,
                }
            except Doctor.DoesNotExist:
                doctor_info = {'error': 'Doctor profile not found'}
        
        # Check chat rooms
        chat_rooms_count = ChatRoom.objects.filter(
            Q(patient__user=user) | Q(doctor__user=user)
        ).count()
        
        return Response({
            'status': 'Chat system is accessible',
            'user': user_info,
            'doctor': doctor_info,
            'chat_rooms_count': chat_rooms_count,
            'timestamp': timezone.now().isoformat(),
        })