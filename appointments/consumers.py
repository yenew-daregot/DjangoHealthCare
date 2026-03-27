"""
WebSocket consumers for real-time appointment updates
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from .models import Appointment
from .serializers import AppointmentSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

class AppointmentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for appointment updates
    Handles real-time notifications for appointment changes
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Get token from query string
            token = self.scope['query_string'].decode().split('token=')[1] if 'token=' in self.scope['query_string'].decode() else None
            
            if not token:
                logger.warning("WebSocket connection rejected: No token provided")
                await self.close()
                return
            
            # Authenticate user
            user = await self.authenticate_user(token)
            if not user or user.is_anonymous:
                logger.warning("WebSocket connection rejected: Invalid token")
                await self.close()
                return
            
            self.user = user
            self.user_id = str(user.id)
            self.user_role = user.role
            
            # Join user-specific group
            self.user_group_name = f"user_{self.user_id}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Join role-specific group
            self.role_group_name = f"role_{self.user_role.lower()}"
            await self.channel_layer.group_add(
                self.role_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"WebSocket connected: User {self.user_id} ({self.user_role})")
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to appointment updates',
                'user_id': self.user_id,
                'user_role': self.user_role
            }))
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if hasattr(self, 'user_group_name'):
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name
                )
            
            if hasattr(self, 'role_group_name'):
                await self.channel_layer.group_discard(
                    self.role_group_name,
                    self.channel_name
                )
            
            # Leave any appointment-specific groups
            if hasattr(self, 'appointment_subscriptions'):
                for appointment_id in self.appointment_subscriptions:
                    await self.channel_layer.group_discard(
                        f"appointment_{appointment_id}",
                        self.channel_name
                    )
            
            logger.info(f"WebSocket disconnected: User {getattr(self, 'user_id', 'unknown')} (code: {close_code})")
            
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {str(e)}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_appointment':
                await self.subscribe_to_appointment(data.get('appointment_id'))
            elif message_type == 'unsubscribe_appointment':
                await self.unsubscribe_from_appointment(data.get('appointment_id'))
            elif message_type == 'subscribe_user_appointments':
                await self.subscribe_to_user_appointments(data.get('user_id'), data.get('user_role'))
            elif message_type == 'heartbeat':
                await self.send(text_data=json.dumps({'type': 'heartbeat_response'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
    
    async def subscribe_to_appointment(self, appointment_id):
        """Subscribe to updates for a specific appointment"""
        if not appointment_id:
            return
        
        # Check if user has permission to view this appointment
        has_permission = await self.check_appointment_permission(appointment_id)
        if not has_permission:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Permission denied for this appointment'
            }))
            return
        
        # Add to appointment-specific group
        group_name = f"appointment_{appointment_id}"
        await self.channel_layer.group_add(group_name, self.channel_name)
        
        # Track subscription
        if not hasattr(self, 'appointment_subscriptions'):
            self.appointment_subscriptions = set()
        self.appointment_subscriptions.add(appointment_id)
        
        logger.info(f"User {self.user_id} subscribed to appointment {appointment_id}")
    
    async def unsubscribe_from_appointment(self, appointment_id):
        """Unsubscribe from updates for a specific appointment"""
        if not appointment_id:
            return
        
        group_name = f"appointment_{appointment_id}"
        await self.channel_layer.group_discard(group_name, self.channel_name)
        
        if hasattr(self, 'appointment_subscriptions'):
            self.appointment_subscriptions.discard(appointment_id)
        
        logger.info(f"User {self.user_id} unsubscribed from appointment {appointment_id}")
    
    async def subscribe_to_user_appointments(self, user_id, user_role):
        """Subscribe to all appointments for a user"""
        if str(user_id) != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Can only subscribe to your own appointments'
            }))
            return
        
        # Already subscribed via user group in connect()
        logger.info(f"User {self.user_id} subscribed to user appointments")
    
    # Message handlers for different types of appointment updates
    async def appointment_updated(self, event):
        """Handle appointment update notifications"""
        await self.send(text_data=json.dumps({
            'type': 'appointment_updated',
            'payload': event['payload']
        }))
    
    async def appointment_created(self, event):
        """Handle appointment creation notifications"""
        await self.send(text_data=json.dumps({
            'type': 'appointment_created',
            'payload': event['payload']
        }))
    
    async def appointment_cancelled(self, event):
        """Handle appointment cancellation notifications"""
        await self.send(text_data=json.dumps({
            'type': 'appointment_cancelled',
            'payload': event['payload']
        }))
    
    async def appointment_confirmed(self, event):
        """Handle appointment confirmation notifications"""
        await self.send(text_data=json.dumps({
            'type': 'appointment_confirmed',
            'payload': event['payload']
        }))
    
    async def notification(self, event):
        """Handle general notifications"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'payload': event['payload']
        }))
    
    @database_sync_to_async
    def authenticate_user(self, token):
        """Authenticate user from JWT token"""
        try:
            # Validate token
            UntypedToken(token)
            
            # Decode token to get user info
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get('user_id')
            
            if user_id:
                user = User.objects.get(id=user_id)
                return user
            
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            logger.error(f"Token authentication failed: {str(e)}")
        
        return AnonymousUser()
    
    @database_sync_to_async
    def check_appointment_permission(self, appointment_id):
        """Check if user has permission to view appointment"""
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Admin can view all appointments
            if self.user_role in ['ADMIN', 'admin']:
                return True
            
            # Doctor can view their appointments
            if self.user_role in ['DOCTOR', 'doctor'] and appointment.doctor.user_id == self.user.id:
                return True
            
            # Patient can view their appointments
            if self.user_role in ['PATIENT', 'patient'] and appointment.patient.user_id == self.user.id:
                return True
            
            return False
            
        except Appointment.DoesNotExist:
            return False


# Utility functions for sending notifications
async def send_appointment_notification(appointment_id, notification_type, data=None):
    """Send appointment notification to relevant users"""
    from channels.layers import get_channel_layer
    
    try:
        appointment = await database_sync_to_async(Appointment.objects.select_related('patient__user', 'doctor__user').get)(id=appointment_id)
        
        # Serialize appointment data
        serializer = AppointmentSerializer(appointment)
        appointment_data = serializer.data
        
        channel_layer = get_channel_layer()
        
        # Prepare notification payload
        payload = {
            'appointment': appointment_data,
            'notification_type': notification_type,
            'timestamp': appointment.updated_at.isoformat() if appointment.updated_at else None,
            **(data or {})
        }
        
        # Send to appointment-specific group
        await channel_layer.group_send(
            f"appointment_{appointment_id}",
            {
                'type': f'appointment_{notification_type}',
                'payload': payload
            }
        )
        
        # Send to patient
        if appointment.patient and appointment.patient.user:
            await channel_layer.group_send(
                f"user_{appointment.patient.user.id}",
                {
                    'type': f'appointment_{notification_type}',
                    'payload': payload
                }
            )
        
        # Send to doctor
        if appointment.doctor and appointment.doctor.user:
            await channel_layer.group_send(
                f"user_{appointment.doctor.user.id}",
                {
                    'type': f'appointment_{notification_type}',
                    'payload': payload
                }
            )
        
        # Send to admin users
        await channel_layer.group_send(
            "role_admin",
            {
                'type': f'appointment_{notification_type}',
                'payload': payload
            }
        )
        
        logger.info(f"Sent {notification_type} notification for appointment {appointment_id}")
        
    except Exception as e:
        logger.error(f"Error sending appointment notification: {str(e)}")


# Signal handlers for automatic notifications
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Appointment)
def appointment_saved(sender, instance, created, **kwargs):
    """Send notification when appointment is saved"""
    try:
        notification_type = 'created' if created else 'updated'
        
        # Run async notification in sync context
        async_to_sync(send_appointment_notification)(
            instance.id,
            notification_type
        )
        
    except Exception as e:
        logger.error(f"Error in appointment_saved signal: {str(e)}")

@receiver(post_delete, sender=Appointment)
def appointment_deleted(sender, instance, **kwargs):
    """Send notification when appointment is deleted"""
    try:
        # Note: instance.id might not be available after deletion
        # This is mainly for cleanup purposes
        logger.info(f"Appointment {instance.id} deleted")
        
    except Exception as e:
        logger.error(f"Error in appointment_deleted signal: {str(e)}")