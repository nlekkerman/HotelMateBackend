from rest_framework import serializers
from .models import MaintenanceRequest, MaintenanceComment, MaintenancePhoto

class MaintenancePhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = MaintenancePhoto
        fields = ['id', 'request', 'image', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class BulkMaintenancePhotoSerializer(serializers.Serializer):
    request = serializers.PrimaryKeyRelatedField(queryset=MaintenanceRequest.objects.all())
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )

    def create(self, validated_data):
        request = validated_data['request']
        user = self.context['request'].user.staff_profile
        photos = []
        for image in validated_data['images']:
            photo = MaintenancePhoto.objects.create(request=request, image=image, uploaded_by=user)
            photos.append(photo)
        return photos

class MaintenanceCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceComment
        fields = ['id', 'message', 'staff', 'created_at']

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    comments = MaintenanceCommentSerializer(many=True, read_only=True)
    photos = MaintenancePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'hotel', 'room', 'location_note', 'title', 'description',
            'reported_by', 'accepted_by', 'status', 'created_at', 'updated_at',
            'comments', 'photos'
        ]
        read_only_fields = ['id', 'hotel', 'reported_by', 'created_at', 'updated_at']

