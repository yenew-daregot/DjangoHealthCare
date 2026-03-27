from rest_framework import serializers
from decimal import Decimal
from .models import (
    UniversityProgram, StudentInsurance, ServiceCategory,
    StudentDebt, Invoice, InvoiceItem, Payment, FeeWaiver, PaymentPlan
)
from patients.serializers import PatientSerializer
from users.serializers import UserSerializer


class UniversityProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniversityProgram
        fields = '__all__'


class StudentInsuranceSerializer(serializers.ModelSerializer):
    student = PatientSerializer(read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = StudentInsurance
        fields = '__all__'
        read_only_fields = ['is_verified', 'verified_until']


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'


class StudentDebtSerializer(serializers.ModelSerializer):
    student = PatientSerializer(read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = StudentDebt
        fields = '__all__'
        read_only_fields = ['debt_number', 'created_at', 'updated_at']


class InvoiceItemSerializer(serializers.ModelSerializer):
    service_category = ServiceCategorySerializer(read_only=True)
    service_category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ['total_price']


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, allow_null=True)
    debt_number = serializers.CharField(source='student_debt.debt_number', read_only=True, allow_null=True)
    student_name = serializers.SerializerMethodField(read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['payment_date', 'receipt_number', 'processed_by']
    
    def get_student_name(self, obj):
        if obj.invoice and obj.invoice.student:
            return obj.invoice.student.user.get_full_name()
        elif obj.student_debt and obj.student_debt.student:
            return obj.student_debt.student.user.get_full_name()
        return None


class FeeWaiverSerializer(serializers.ModelSerializer):
    student = PatientSerializer(read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, allow_null=True)
    debt_number = serializers.CharField(source='student_debt.debt_number', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FeeWaiver
        fields = '__all__'
        read_only_fields = ['approved_date', 'created_at', 'approved_by']


class PaymentPlanSerializer(serializers.ModelSerializer):
    student_debt = StudentDebtSerializer(read_only=True)
    student_debt_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PaymentPlan
        fields = '__all__'
        read_only_fields = ['created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    student = PatientSerializer(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = [
            'invoice_number', 'created_at', 'updated_at', 'balance_due',
            'subtotal', 'total_amount', 'amount_paid', 'created_by'
        ]


class CreateInvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'student_id', 'appointment', 'lab_request', 'service_description',
            'due_date', 'semester', 'academic_year', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)
        
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        return invoice


class ProcessPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['invoice', 'student_debt', 'amount', 'payment_method', 'transaction_id', 'notes']
    
    def validate(self, data):
        invoice = data.get('invoice')
        student_debt = data.get('student_debt')
        amount = data.get('amount', Decimal('0.00'))
        
        if not invoice and not student_debt:
            raise serializers.ValidationError("Either invoice or student_debt must be provided.")
        
        if amount <= Decimal('0.00'):
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        
        if invoice and amount > invoice.balance_due:
            raise serializers.ValidationError("Payment amount cannot exceed invoice balance.")
        
        if student_debt and amount > student_debt.outstanding_balance:
            raise serializers.ValidationError("Payment amount cannot exceed debt balance.")
        
        return data


class RequestFeeWaiverSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeWaiver
        fields = ['student_id', 'invoice', 'student_debt', 'waiver_type', 'reason', 'requested_amount', 'notes']
    
    def validate(self, data):
        student_id = data.get('student_id')
        invoice = data.get('invoice')
        student_debt = data.get('student_debt')
        
        if not invoice and not student_debt:
            raise serializers.ValidationError("Either invoice or student_debt must be provided.")
        
        return data


class BillingSummarySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    academic_year = serializers.CharField()
    total_invoices = serializers.IntegerField()
    total_debts = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))
    overdue_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))
    waiver_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))