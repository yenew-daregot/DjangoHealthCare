from django.contrib import admin
from .models import (
    UniversityProgram, StudentInsurance, ServiceCategory,
    Invoice, InvoiceItem, Payment, StudentDebt, 
    FeeWaiver, PaymentPlan
)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ['total_price']

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['payment_date', 'receipt_number']
    fields = ['amount', 'payment_method', 'status', 'transaction_id', 'payment_date']

@admin.register(UniversityProgram)
class UniversityProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_type', 'department', 'tuition_coverage', 'is_active']
    list_filter = ['program_type', 'is_active']
    search_fields = ['name', 'department']
    list_editable = ['is_active']

@admin.register(StudentInsurance)
class StudentInsuranceAdmin(admin.ModelAdmin):
    list_display = ['student', 'insurance_type', 'policy_number', 'coverage_percentage', 'is_verified', 'is_active']
    list_filter = ['insurance_type', 'is_verified', 'is_active']
    search_fields = ['student__user__username', 'student__user__email', 'policy_number']
    list_editable = ['is_verified', 'is_active']

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'base_price', 'student_price', 'is_active']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'category_type']
    list_editable = ['is_active']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'total_amount', 'amount_paid', 'balance_due', 'status', 'issue_date', 'due_date']
    list_filter = ['status', 'payment_method', 'issue_date', 'due_date', 'semester']
    search_fields = ['invoice_number', 'student__user__username', 'student__user__email']
    readonly_fields = ['created_at', 'updated_at', 'balance_due', 'invoice_number']
    inlines = [InvoiceItemInline, PaymentInline]
    date_hierarchy = 'issue_date'
    list_per_page = 20

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'service_category', 'quantity', 'unit_price', 'total_price']
    list_filter = ['service_category']
    search_fields = ['invoice__invoice_number', 'description']
    readonly_fields = ['total_price']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'invoice', 'student_debt', 'amount', 'payment_method', 'status', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['receipt_number', 'invoice__invoice_number', 'transaction_id']
    readonly_fields = ['payment_date', 'receipt_number']
    list_per_page = 20

@admin.register(StudentDebt)
class StudentDebtAdmin(admin.ModelAdmin):
    list_display = ['debt_number', 'student', 'original_amount', 'outstanding_balance', 'status', 'due_date', 'is_urgent']
    list_filter = ['status', 'academic_year', 'semester', 'is_urgent']
    search_fields = ['debt_number', 'student__user__username']
    readonly_fields = ['debt_number', 'created_at', 'updated_at']
    list_editable = ['status', 'is_urgent']

@admin.register(FeeWaiver)
class FeeWaiverAdmin(admin.ModelAdmin):
    list_display = ['student', 'waiver_type', 'requested_amount', 'approved_amount', 'status', 'approved_date', 'created_at']
    list_filter = ['waiver_type', 'status', 'approved_date']
    search_fields = ['student__user__username', 'reason', 'notes']
    readonly_fields = ['created_at']
    list_editable = ['status', 'approved_amount']

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['student_debt', 'total_amount', 'installment_amount', 'number_of_installments', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['student_debt__debt_number', 'student_debt__student__user__username']
    readonly_fields = ['created_at']