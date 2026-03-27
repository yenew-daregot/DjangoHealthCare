from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from . import views

@api_view(['GET'])
@permission_classes([AllowAny])
def chat_root(request):
    """
    Secure Medical Chat System API Root
    Real-time encrypted messaging system for patient-doctor communication
    """
    base_url = request.build_absolute_uri('/api/chat')
    
    endpoints = {
        "api": "Secure Medical Chat & Messaging System",
        "version": "1.0",
        "description": "Real-time, encrypted, HIPAA-compliant messaging system for secure patient-doctor communication",
        "purpose": "Enable secure communication between patients and healthcare providers while maintaining privacy and audit trails",
        
        "compliance_features": [
            "HIPAA-compliant message encryption",
            "End-to-end encryption for sensitive data",
            "Message audit trails and logging",
            "Secure file attachments with encryption",
            "Access control and role-based permissions",
            "Message retention policies",
            "Secure WebSocket connections"
        ],
        
        "key_functionalities": [
            "Secure chat room creation and management",
            "Real-time messaging with WebSocket support",
            "File sharing with encryption",
            "Read receipts and message status tracking",
            "Chat notifications and alerts",
            "Participant management",
            "Message search and filtering",
            "Chat history with pagination"
        ],
        
        "endpoints": {
            "chat_rooms": {
                "description": "Manage secure chat rooms for medical conversations",
                "list_create": f"{base_url}/rooms/",
                "methods": ["GET", "POST"],
                "retrieve_update_destroy": f"{base_url}/rooms/{{id}}/",
                "patient_rooms": f"{base_url}/rooms/patient/{{patient_id}}/",
                "doctor_rooms": f"{base_url}/rooms/doctor/{{doctor_id}}/",
                "find_or_create": f"{base_url}/rooms/find-or-create/",
                "details": "Automatically creates rooms between patients and doctors"
            },
            
            "messages": {
                "description": "Secure message management with encryption",
                "list_create": f"{base_url}/messages/",
                "methods": ["GET", "POST"],
                "retrieve": f"{base_url}/messages/{{id}}/",
                "room_messages": f"{base_url}/rooms/{{room_id}}/messages/",
                "mark_read": f"{base_url}/messages/{{id}}/mark-read/",
                "mark_all_read": f"{base_url}/rooms/{{room_id}}/mark-all-read/",
                "security_note": "All messages are encrypted at rest and in transit"
            },
            
            "file_management": {
                "description": "Secure file upload and sharing for medical documents",
                "upload": f"{base_url}/upload-file/",
                "methods": ["POST"],
                "supported_formats": ["pdf", "jpg", "png", "doc", "docx", "txt"],
                "max_size": "10MB per file",
                "encryption": "Files are encrypted before storage"
            },
            
            "participants": {
                "description": "Manage chat room participants and permissions",
                "room_participants": f"{base_url}/rooms/{{room_id}}/participants/",
                "methods": ["GET"],
                "participant_detail": f"{base_url}/participants/{{id}}/",
                "methods_detail": ["GET", "PUT", "PATCH", "DELETE"],
                "roles": ["patient", "doctor", "nurse", "admin", "family_member"]
            },
            
            "notifications": {
                "description": "Real-time chat notifications and alerts",
                "list": f"{base_url}/notifications/",
                "methods": ["GET"],
                "mark_read": f"{base_url}/notifications/{{id}}/mark-read/",
                "mark_all_read": f"{base_url}/notifications/mark-all-read/",
                "types": ["new_message", "file_uploaded", "participant_joined", "room_created"]
            },
            
            "real_time_features": {
                "description": "WebSocket support for real-time communication",
                "websocket_token": f"{base_url}/websocket-token/",
                "methods": ["POST"],
                "purpose": "Get authentication token for WebSocket connection",
                "websocket_url": "ws://127.0.0.1:8000/ws/chat/{{room_id}}/",
                "protocol": "wss:// for production (secure WebSocket)"
            }
        },
        
        "communication_workflows": {
            "patient_doctor_chat": {
                "1": "Find or create chat room: POST /api/chat/rooms/find-or-create/",
                "2": "Send message: POST /api/chat/messages/",
                "3": "Upload medical file: POST /api/chat/upload-file/",
                "4": "Check notifications: GET /api/chat/notifications/"
            },
            "medical_team_discussion": {
                "1": "Create multi-participant room: POST /api/chat/rooms/",
                "2": "Add participants: See room participants endpoints",
                "3": "Share lab results: Upload files via file upload",
                "4": "Track message status: Use read receipts"
            },
            "patient_support": {
                "1": "View patient chat history: GET /api/chat/rooms/patient/{patient_id}/",
                "2": "Check unread messages: GET /api/chat/notifications/",
                "3": "Mark messages as read: Use mark-read endpoints"
            }
        },
        
        "security_measures": {
            "encryption": {
                "message_encryption": "AES-256 encryption for message content",
                "file_encryption": "Encrypted storage for all attachments",
                "transit_encryption": "TLS 1.3 for HTTP, WSS for WebSocket"
            },
            "authentication": "JWT Bearer token required for all endpoints",
            "authorization": "Role-based access control (RBAC)",
            "audit_logging": "All message operations are logged with timestamps",
            "data_retention": "Configurable message retention policies"
        },
        
        "webSocket_integration": {
            "connection_flow": "1. Get WebSocket token → 2. Connect to WebSocket URL → 3. Send/receive real-time messages",
            "events": {
                "message": "New message received",
                "typing": "User is typing indicator",
                "read_receipt": "Message read confirmation",
                "user_online": "User online status",
                "file_uploaded": "File upload notification"
            },
            "reconnection": "Automatic reconnection with token refresh"
        },
        
        "message_types": {
            "text": "Plain text messages",
            "file": "Attached files with metadata",
            "system": "System notifications (user joined, room created, etc.)",
            "medical_alert": "Priority medical notifications",
            "prescription": "Prescription-related messages"
        },
        
        "rate_limiting": {
            "messages": "100 messages per minute per user",
            "file_uploads": "10 files per hour per user",
            "room_creation": "5 rooms per day per user"
        },
        
        "authentication": {
            "required": "Yes, for all endpoints",
            "methods": ["JWT Bearer Token"],
            "get_token": "POST /api/auth/token/ with username and password",
            "websocket_auth": "POST /api/chat/websocket-token/ to get WebSocket token",
            "permission_levels": ["patient", "doctor", "nurse", "admin", "family_member"]
        },
        
        "support": {
            "technical_support": "chat-support@hospital.com",
            "security_concerns": "security@hospital.com",
            "emergency_bypass": "For urgent medical communication issues",
            "documentation": "https://docs.hospital-chat-api.com",
            "privacy_policy": "https://hospital.com/chat-privacy"
        },
        
        "compliance": {
            "hipaa": "Fully HIPAA-compliant for protected health information (PHI)",
            "gdpr": "GDPR-compliant for European users",
            "audit_ready": "Complete audit trails for all communications",
            "data_encryption": "Encryption at rest and in transit"
        }
    }
    
    return Response(endpoints)

urlpatterns = [
    # Root endpoint - must be first
    path('', chat_root, name='chat-root'),
    
    # Chat Rooms
    path('rooms/', views.ChatRoomListCreateView.as_view(), name='chat-room-list'),
    path('rooms/<int:pk>/', views.ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/patient/<int:patient_id>/', views.PatientChatRoomsView.as_view(), name='patient-chat-rooms'),
    path('rooms/doctor/<int:doctor_id>/', views.DoctorChatRoomsView.as_view(), name='doctor-chat-rooms'),
    path('rooms/find-or-create/', views.FindOrCreateChatRoomView.as_view(), name='find-or-create-chat-room'),
    
    # Messages
    path('messages/', views.MessageListCreateView.as_view(), name='message-list'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('rooms/<int:room_id>/messages/', views.RoomMessagesView.as_view(), name='room-messages'),
    path('messages/<int:pk>/mark-read/', views.MarkMessageReadView.as_view(), name='mark-message-read'),
    path('rooms/<int:room_id>/mark-all-read/', views.MarkAllMessagesReadView.as_view(), name='mark-all-messages-read'),
    
    # File Upload
    path('upload-file/', views.FileUploadView.as_view(), name='file-upload'),
    
    # Participants
    path('rooms/<int:room_id>/participants/', views.RoomParticipantsView.as_view(), name='room-participants'),
    path('participants/<int:pk>/', views.ParticipantDetailView.as_view(), name='participant-detail'),
    
    # Notifications
    path('notifications/', views.ChatNotificationListView.as_view(), name='chat-notification-list'),
    path('notifications/<int:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    
    # WebSocket Token (for real-time chat)
    path('websocket-token/', views.WebSocketTokenView.as_view(), name='websocket-token'),
    
    # Test endpoint for debugging
    path('test/', views.ChatTestView.as_view(), name='chat-test'),
]