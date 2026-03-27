from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .views import *

@api_view(['GET'])
@permission_classes([AllowAny])
def billing_root(request):
    """
    University Billing and Finance Management System API Root
    Comprehensive billing, invoicing, and financial management for university healthcare services
    """
    base_url = request.build_absolute_uri('/api/billing')
    
    endpoints = {
        "api": "University Billing & Finance Management System",
        "version": "1.0",
        "description": "Comprehensive billing, invoicing, payment processing, and financial management system for university healthcare services",
        "purpose": "Manage student medical billing, insurance claims, payments, and financial reporting",
        
        "system_features": [
            "University program and department management",
            "Student health insurance tracking",
            "Medical service categorization and pricing",
            "Invoice generation and management",
            "Payment processing and reconciliation",
            "Student debt tracking and management",
            "Fee waiver requests and approvals",
            "Comprehensive financial reporting",
            "Revenue tracking and analytics"
        ],
        
        "target_users": [
            "University administrators",
            "Finance department staff",
            "Student health services",
            "Insurance coordinators",
            "Student accounts office",
            "Auditors and financial controllers"
        ],
        
        "endpoints": {
            "university_programs": {
                "description": "Manage university programs and departments",
                "list": f"{base_url}/university-programs/",
                "methods": ["GET"]
            },
            
            "student_insurance": {
                "description": "Student health insurance management",
                "list_create": f"{base_url}/insurance/",
                "retrieve_update_destroy": f"{base_url}/insurance/{{id}}/",
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"]
            },
            
            "service_categories": {
                "description": "Medical service categories and pricing",
                "list": f"{base_url}/service-categories/",
                "methods": ["GET"]
            },
            
            "student_debts": {
                "description": "Student medical debt tracking and management",
                "list": f"{base_url}/debts/",
                "retrieve": f"{base_url}/debts/{{id}}/",
                "methods": ["GET"]
            },
            
            "invoices": {
                "description": "Medical service invoice management",
                "list_create": f"{base_url}/invoices/",
                "retrieve_update_destroy": f"{base_url}/invoices/{{id}}/",
                "create_with_items": f"{base_url}/invoices/create-with-items/",
                "methods": {
                    "list": ["GET", "POST"],
                    "detail": ["GET", "PUT", "PATCH", "DELETE"],
                    "create_with_items": ["POST"]
                }
            },
            
            "payments": {
                "description": "Payment processing and management",
                "list_create": f"{base_url}/payments/",
                "process_payment": f"{base_url}/process-payment/",
                "methods": {
                    "list": ["GET", "POST"],
                    "process": ["POST"]
                }
            },
            
            "fee_waivers": {
                "description": "Fee waiver requests and approvals",
                "list_create": f"{base_url}/fee-waivers/",
                "request_waiver": f"{base_url}/request-waiver/",
                "methods": {
                    "list": ["GET", "POST"],
                    "request": ["POST"]
                }
            },
            
            "reports_and_actions": {
                "description": "Financial reports and billing actions",
                "student_summary": f"{base_url}/summary/{{student_id}}/",
                "revenue_report": f"{base_url}/revenue-report/",
                "outstanding_debts": f"{base_url}/outstanding-debts/",
                "convert_to_debt": f"{base_url}/convert-to-debt/{{invoice_id}}/",
                "methods": {
                    "summary": ["GET"],
                    "reports": ["GET"],
                    "convert": ["POST"]
                }
            }
        },
        
        "workflow_examples": {
            "new_medical_service": {
                "1": "Check service category pricing: GET /api/billing/service-categories/",
                "2": "Create invoice: POST /api/billing/invoices/create-with-items/",
                "3": "Check student insurance: GET /api/billing/insurance/?student_id={id}",
                "4": "Process payment: POST /api/billing/process-payment/"
            },
            "student_financial_inquiry": {
                "1": "View billing summary: GET /api/billing/summary/{student_id}/",
                "2": "Check outstanding debts: GET /api/billing/outstanding-debts/?student_id={id}",
                "3": "Request fee waiver: POST /api/billing/request-waiver/"
            },
            "financial_reporting": {
                "1": "Generate revenue report: GET /api/billing/revenue-report/",
                "2": "View outstanding debts: GET /api/billing/outstanding-debts/",
                "3": "Check university program finances: GET /api/billing/university-programs/"
            }
        },
        
        "financial_entities": {
            "Invoice": "Bill for medical services provided",
            "Payment": "Record of payment received",
            "StudentDebt": "Outstanding balance owed by student",
            "FeeWaiver": "Approved reduction or elimination of fees",
            "StudentInsurance": "Student health insurance coverage details",
            "ServiceCategory": "Medical service types and standard pricing",
            "UniversityProgram": "Academic programs/departments for billing allocation"
        },
        
        "authentication": {
            "required": "Yes, for all endpoints",
            "methods": ["JWT Bearer Token", "Session Authentication"],
            "get_token": "POST /api/auth/token/ with username and password",
            "refresh_token": "POST /api/auth/token/refresh/ with refresh token",
            "permission_notes": "Different endpoints may require different permission levels (admin, finance_staff, student)"
        },
        
        "data_models": {
            "invoice_statuses": ["draft", "issued", "paid", "overdue", "cancelled", "converted_to_debt"],
            "payment_methods": ["cash", "credit_card", "debit_card", "bank_transfer", "insurance_claim", "scholarship", "waiver"],
            "waiver_statuses": ["pending", "approved", "rejected", "partially_approved"],
            "insurance_statuses": ["active", "expired", "pending_verification", "suspended"]
        },
        
        "integration_points": {
            "student_information_system": "Sync student data and program information",
            "medical_records_system": "Link services to medical records",
            "accounting_software": "Export financial data",
            "insurance_portals": "Submit insurance claims electronically",
            "payment_gateways": "Online payment processing"
        },
        
        "support": {
            "finance_helpdesk": "finance-support@university.edu",
            "student_accounts": "student-accounts@university.edu",
            "phone_support": "+1-800-UNIV-BILL",
            "emergency_billing": "For urgent billing issues during business hours",
            "documentation": "https://docs.university-billing-api.edu"
        }
    }
    
    return Response(endpoints)

urlpatterns = [
    # Root endpoint - must be first
    path('', billing_root, name='billing-root'),
    
    # University Programs
    path('university-programs/', UniversityProgramListView.as_view(), name='university-programs'),
    
    # Student Insurance
    path('insurance/', StudentInsuranceListCreateView.as_view(), name='insurance-list'),
    path('insurance/<int:pk>/', StudentInsuranceDetailView.as_view(), name='insurance-detail'),
    
    # Service Categories
    path('service-categories/', ServiceCategoryListView.as_view(), name='service-categories'),
    
    # Student Debts
    path('debts/', StudentDebtListView.as_view(), name='debt-list'),
    path('debts/<int:pk>/', StudentDebtDetailView.as_view(), name='debt-detail'),
    
    # Invoices
    path('invoices/', InvoiceListCreateView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/create-with-items/', CreateInvoiceWithItemsView.as_view(), name='create-invoice-with-items'),
    
    # Payments
    path('payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('process-payment/', ProcessPaymentView.as_view(), name='process-payment'),
    
    # Fee Waivers
    path('fee-waivers/', FeeWaiverListCreateView.as_view(), name='fee-waiver-list'),
    path('request-waiver/', RequestFeeWaiverView.as_view(), name='request-waiver'),
    
    # Reports and Actions
    path('summary/<int:student_id>/', StudentBillingSummaryView.as_view(), name='billing-summary'),
    path('revenue-report/', RevenueReportView.as_view(), name='revenue-report'),
    path('outstanding-debts/', OutstandingDebtsReportView.as_view(), name='outstanding-debts'),
    path('convert-to-debt/<int:invoice_id>/', ConvertToDebtView.as_view(), name='convert-to-debt'),
    
    # Waiver Actions
    path('approve-waiver/<int:waiver_id>/', ApproveWaiverView.as_view(), name='approve-waiver'),
    path('reject-waiver/<int:waiver_id>/', RejectWaiverView.as_view(), name='reject-waiver'),
    
    # Integration Endpoints
    path('create-invoice-from-appointment/<int:appointment_id>/', CreateInvoiceFromAppointmentView.as_view(), name='create-invoice-from-appointment'),
    path('create-invoice-from-lab/<int:lab_request_id>/', CreateInvoiceFromLabRequestView.as_view(), name='create-invoice-from-lab'),
    
    # Bulk Actions
    path('bulk-invoice-actions/', BulkInvoiceActionsView.as_view(), name='bulk-invoice-actions'),
    
    # Payment Plans
    path('payment-plans/', PaymentPlanCreateView.as_view(), name='payment-plan-create'),
    
    # Dashboard
    path('dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
]