from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    UniversityProgram, StudentInsurance, ServiceCategory,
    StudentDebt, Invoice, InvoiceItem, Payment, FeeWaiver, PaymentPlan
)
from .serializers import *
from .utils import generate_invoice_number, generate_debt_number


# University Program Views
class UniversityProgramListView(generics.ListAPIView):
    queryset = UniversityProgram.objects.filter(is_active=True)
    serializer_class = UniversityProgramSerializer
    permission_classes = [permissions.IsAuthenticated]


# Student Insurance Views
class StudentInsuranceListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentInsuranceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return StudentInsurance.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return StudentInsurance.objects.all()
        return StudentInsurance.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()


class StudentInsuranceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudentInsuranceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return StudentInsurance.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return StudentInsurance.objects.all()
        return StudentInsurance.objects.none()


# Service Categories
class ServiceCategoryListView(generics.ListAPIView):
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# Student Debt Views
class StudentDebtListView(generics.ListAPIView):
    serializer_class = StudentDebtSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return StudentDebt.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return StudentDebt.objects.all()
        return StudentDebt.objects.none()


class StudentDebtDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentDebtSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return StudentDebt.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return StudentDebt.objects.all()
        return StudentDebt.objects.none()


# Invoice Views
class InvoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return Invoice.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return Invoice.objects.all()
        return Invoice.objects.none()
    
    def perform_create(self, serializer):
        invoice_number = generate_invoice_number()
        serializer.save(
            created_by=self.request.user, 
            invoice_number=invoice_number,
            issue_date=timezone.now().date()
        )


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return Invoice.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return Invoice.objects.all()
        return Invoice.objects.none()


class CreateInvoiceWithItemsView(generics.CreateAPIView):
    serializer_class = CreateInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        invoice_number = generate_invoice_number()
        instance = serializer.save(
            created_by=self.request.user, 
            invoice_number=invoice_number,
            issue_date=timezone.now().date()
        )
        instance.save()


# Payment Views
class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return Payment.objects.filter(
                Q(invoice__student__user=user) | 
                Q(student_debt__student__user=user)
            )
        elif user.user_type in ['admin', 'staff']:
            return Payment.objects.all()
        return Payment.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(processed_by=self.request.user)


class ProcessPaymentView(generics.CreateAPIView):
    serializer_class = ProcessPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(
            processed_by=self.request.user, 
            status='completed',
            payment_date=timezone.now()
        )


# Fee Waiver Views
class FeeWaiverListCreateView(generics.ListCreateAPIView):
    serializer_class = FeeWaiverSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'patient':
            return FeeWaiver.objects.filter(student__user=user)
        elif user.user_type in ['admin', 'staff']:
            return FeeWaiver.objects.all()
        return FeeWaiver.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()


class RequestFeeWaiverView(generics.CreateAPIView):
    serializer_class = RequestFeeWaiverSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(status='pending')


# Student Billing Summary
class StudentBillingSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, student_id):
        try:
            # Verify permission
            user = request.user
            if user.user_type == 'patient' and user.patient.id != student_id:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            current_year = timezone.now().year
            academic_year = f"{current_year}-{current_year + 1}"
            
            # Calculate totals
            invoices = Invoice.objects.filter(student_id=student_id)
            debts = StudentDebt.objects.filter(student_id=student_id)
            waivers = FeeWaiver.objects.filter(student_id=student_id, status='approved')
            
            total_invoices = invoices.count()
            total_debts = debts.count()
            total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            total_paid = invoices.aggregate(paid=Sum('amount_paid'))['paid'] or Decimal('0.00')
            outstanding_balance = max(total_amount - total_paid, Decimal('0.00'))
            overdue_amount = debts.filter(status='overdue').aggregate(
                total=Sum('outstanding_balance')
            )['total'] or Decimal('0.00')
            waiver_amount = waivers.aggregate(total=Sum('approved_amount'))['total'] or Decimal('0.00')
            
            summary_data = {
                'student_id': student_id,
                'academic_year': academic_year,
                'total_invoices': total_invoices,
                'total_debts': total_debts,
                'total_amount': total_amount,
                'total_paid': total_paid,
                'outstanding_balance': outstanding_balance,
                'overdue_amount': overdue_amount,
                'waiver_amount': waiver_amount,
            }
            
            serializer = BillingSummarySerializer(summary_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# Reports
class RevenueReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type not in ['admin', 'staff']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        start_date = request.GET.get('start_date', timezone.now().replace(day=1).date())
        end_date = request.GET.get('end_date', timezone.now().date())
        
        payments = Payment.objects.filter(
            status='completed',
            payment_date__date__range=[start_date, end_date]
        )
        
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        payment_count = payments.count()
        average_payment = total_revenue / payment_count if payment_count > 0 else Decimal('0.00')
        
        revenue_data = {
            'total_revenue': total_revenue,
            'payment_count': payment_count,
            'average_payment': average_payment,
            'start_date': start_date,
            'end_date': end_date,
        }
        
        return Response(revenue_data)


class OutstandingDebtsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type not in ['admin', 'staff']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        debts = StudentDebt.objects.filter(outstanding_balance__gt=0)
        
        total_outstanding = debts.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
        debt_count = debts.count()
        average_debt = total_outstanding / debt_count if debt_count > 0 else Decimal('0.00')
        
        overdue_debts = debts.filter(status='overdue')
        overdue_count = overdue_debts.count()
        total_overdue = overdue_debts.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
        
        outstanding_data = {
            'total_outstanding': total_outstanding,
            'debt_count': debt_count,
            'average_debt': average_debt,
            'overdue_count': overdue_count,
            'total_overdue': total_overdue,
        }
        
        return Response(outstanding_data)


class ConvertToDebtView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, invoice_id):
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            
            if invoice.balance_due <= 0:
                return Response(
                    {'error': 'Invoice has no outstanding balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            debt = invoice.create_student_debt()
            
            if debt:
                return Response({
                    'message': 'Invoice successfully converted to student debt',
                    'debt': StudentDebtSerializer(debt).data
                })
            else:
                return Response(
                    {'error': 'Could not convert invoice to debt'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# Additional API endpoints for better integration

class ApproveWaiverView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, waiver_id):
        if request.user.user_type not in ['admin', 'staff']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            waiver = FeeWaiver.objects.get(id=waiver_id)
            approved_amount = request.data.get('approved_amount', waiver.requested_amount)
            
            waiver.status = 'approved'
            waiver.approved_amount = Decimal(str(approved_amount))
            waiver.approved_by = request.user
            waiver.approved_date = timezone.now()
            waiver.save()
            
            return Response({
                'message': 'Waiver approved successfully',
                'waiver': FeeWaiverSerializer(waiver).data
            })
            
        except FeeWaiver.DoesNotExist:
            return Response(
                {'error': 'Waiver not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RejectWaiverView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, waiver_id):
        if request.user.user_type not in ['admin', 'staff']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            waiver = FeeWaiver.objects.get(id=waiver_id)
            rejection_reason = request.data.get('reason', '')
            
            waiver.status = 'rejected'
            waiver.approved_amount = Decimal('0.00')
            waiver.approved_by = request.user
            waiver.approved_date = timezone.now()
            waiver.notes = f"Rejected: {rejection_reason}"
            waiver.save()
            
            return Response({
                'message': 'Waiver rejected',
                'waiver': FeeWaiverSerializer(waiver).data
            })
            
        except FeeWaiver.DoesNotExist:
            return Response(
                {'error': 'Waiver not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CreateInvoiceFromAppointmentView(APIView):
    """Create invoice automatically from completed appointment"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, appointment_id):
        try:
            from appointments.models import Appointment
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Check if invoice already exists
            existing_invoice = Invoice.objects.filter(appointment=appointment).first()
            if existing_invoice:
                return Response({
                    'message': 'Invoice already exists for this appointment',
                    'invoice': InvoiceSerializer(existing_invoice).data
                })
            
            # Get consultation service category
            consultation_category = ServiceCategory.objects.filter(
                category_type='consultation'
            ).first()
            
            if not consultation_category:
                return Response(
                    {'error': 'Consultation service category not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create invoice
            invoice_number = generate_invoice_number()
            due_date = timezone.now().date() + timedelta(days=30)
            
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                student=appointment.patient,
                appointment=appointment,
                service_description=f"Medical consultation with Dr. {appointment.doctor.user.get_full_name()}",
                due_date=due_date,
                created_by=request.user
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                service_category=consultation_category,
                description=f"Consultation - {appointment.appointment_type}",
                quantity=1,
                unit_price=consultation_category.student_price
            )
            
            return Response({
                'message': 'Invoice created successfully',
                'invoice': InvoiceSerializer(invoice).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateInvoiceFromLabRequestView(APIView):
    """Create invoice automatically from completed lab request"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, lab_request_id):
        try:
            from labs.models import LabRequest
            lab_request = LabRequest.objects.get(id=lab_request_id)
            
            # Check if invoice already exists
            existing_invoice = Invoice.objects.filter(lab_request=lab_request).first()
            if existing_invoice:
                return Response({
                    'message': 'Invoice already exists for this lab request',
                    'invoice': InvoiceSerializer(existing_invoice).data
                })
            
            # Get laboratory service category
            lab_category = ServiceCategory.objects.filter(
                category_type='laboratory'
            ).first()
            
            if not lab_category:
                return Response(
                    {'error': 'Laboratory service category not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create invoice
            invoice_number = generate_invoice_number()
            due_date = timezone.now().date() + timedelta(days=30)
            
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                student=lab_request.patient,
                lab_request=lab_request,
                service_description=f"Laboratory tests: {lab_request.test_type}",
                due_date=due_date,
                created_by=request.user
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                service_category=lab_category,
                description=f"Lab Test - {lab_request.test_type}",
                quantity=1,
                unit_price=lab_category.student_price
            )
            
            return Response({
                'message': 'Invoice created successfully',
                'invoice': InvoiceSerializer(invoice).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BulkInvoiceActionsView(APIView):
    """Bulk actions for invoices (mark as sent, convert to debt, etc.)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.user_type not in ['admin', 'staff']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = request.data.get('action')
        invoice_ids = request.data.get('invoice_ids', [])
        
        if not action or not invoice_ids:
            return Response(
                {'error': 'Action and invoice_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoices = Invoice.objects.filter(id__in=invoice_ids)
        results = []
        
        for invoice in invoices:
            try:
                if action == 'mark_sent':
                    invoice.status = 'sent'
                    invoice.save()
                    results.append({'id': invoice.id, 'status': 'success', 'message': 'Marked as sent'})
                
                elif action == 'convert_to_debt':
                    if invoice.balance_due > 0:
                        debt = invoice.create_student_debt()
                        if debt:
                            results.append({'id': invoice.id, 'status': 'success', 'message': 'Converted to debt'})
                        else:
                            results.append({'id': invoice.id, 'status': 'error', 'message': 'Could not convert to debt'})
                    else:
                        results.append({'id': invoice.id, 'status': 'error', 'message': 'No outstanding balance'})
                
                elif action == 'cancel':
                    invoice.status = 'cancelled'
                    invoice.save()
                    results.append({'id': invoice.id, 'status': 'success', 'message': 'Cancelled'})
                
                else:
                    results.append({'id': invoice.id, 'status': 'error', 'message': 'Unknown action'})
                    
            except Exception as e:
                results.append({'id': invoice.id, 'status': 'error', 'message': str(e)})
        
        return Response({'results': results})


class PaymentPlanCreateView(generics.CreateAPIView):
    serializer_class = PaymentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Update student debt status to payment_plan
        payment_plan = serializer.save()
        debt = payment_plan.student_debt
        debt.status = 'payment_plan'
        debt.save()


class FinancialDashboardView(APIView):
    """Comprehensive financial dashboard data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type not in ['admin', 'staff']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate comprehensive metrics
        today = timezone.now().date()
        current_month = today.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        # Revenue metrics
        current_month_revenue = Payment.objects.filter(
            status='completed',
            payment_date__date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        last_month_revenue = Payment.objects.filter(
            status='completed',
            payment_date__date__gte=last_month,
            payment_date__date__lt=current_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Outstanding metrics
        total_outstanding = StudentDebt.objects.filter(
            outstanding_balance__gt=0
        ).aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
        
        overdue_amount = StudentDebt.objects.filter(
            status='overdue'
        ).aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
        
        # Invoice metrics
        total_invoices = Invoice.objects.count()
        pending_invoices = Invoice.objects.filter(
            status__in=['draft', 'sent', 'pending_insurance']
        ).count()
        
        # Payment metrics
        total_payments = Payment.objects.filter(status='completed').count()
        pending_payments = Payment.objects.filter(status='pending').count()
        
        # Waiver metrics
        pending_waivers = FeeWaiver.objects.filter(status='pending').count()
        
        # Calculate growth rates
        revenue_growth = 0
        if last_month_revenue > 0:
            revenue_growth = float((current_month_revenue - last_month_revenue) / last_month_revenue * 100)
        
        dashboard_data = {
            'revenue': {
                'current_month': current_month_revenue,
                'last_month': last_month_revenue,
                'growth_rate': revenue_growth
            },
            'outstanding': {
                'total_outstanding': total_outstanding,
                'overdue_amount': overdue_amount,
                'overdue_percentage': float(overdue_amount / total_outstanding * 100) if total_outstanding > 0 else 0
            },
            'invoices': {
                'total': total_invoices,
                'pending': pending_invoices,
                'completion_rate': float((total_invoices - pending_invoices) / total_invoices * 100) if total_invoices > 0 else 0
            },
            'payments': {
                'total': total_payments,
                'pending': pending_payments
            },
            'waivers': {
                'pending': pending_waivers
            }
        }
        
        return Response(dashboard_data)