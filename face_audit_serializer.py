# Face Audit Log Serializer - temporary file
from rest_framework import serializers
from attendance.models import FaceAuditLog


class FaceAuditLogSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FaceAuditLog
        fields = [
            'id', 'hotel', 'staff', 'staff_name', 'action', 
            'performed_by', 'performed_by_name', 'reason', 
            'consent_given', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"
    
    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return "System"