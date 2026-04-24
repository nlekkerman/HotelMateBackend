from rest_framework import serializers

from rooms.models import Room
from staff.models import Staff
from staff.serializers import StaffSerializer

from .models import MaintenanceComment, MaintenancePhoto, MaintenanceRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request_hotel(serializer):
    """
    Resolve the acting staff member's hotel from the DRF context.

    Returns the Hotel instance or None if the request/user is missing. The
    caller is expected to fail-closed when None is returned.
    """
    request = serializer.context.get('request') if serializer.context else None
    if request is None:
        return None
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    staff = getattr(user, 'staff_profile', None)
    if staff is None:
        return None
    return getattr(staff, 'hotel', None)


_FOREIGN_REQUEST_ERROR = "Maintenance request not found."
_FOREIGN_ROOM_ERROR = "Room not found."
_FOREIGN_STAFF_ERROR = "Staff member not found."


class _HotelScopedRequestField(serializers.PrimaryKeyRelatedField):
    """
    PrimaryKeyRelatedField for `MaintenanceRequest` that fails identically
    on missing vs. cross-hotel PKs so foreign-hotel existence cannot be
    probed.
    """

    default_error_messages = {
        'required': _FOREIGN_REQUEST_ERROR,
        'does_not_exist': _FOREIGN_REQUEST_ERROR,
        'incorrect_type': _FOREIGN_REQUEST_ERROR,
    }

    def __init__(self, **kwargs):
        kwargs.setdefault('queryset', MaintenanceRequest.objects.all())
        super().__init__(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        hotel = _request_hotel(self.parent) if self.parent else None
        if hotel is None:
            return qs.none()
        return qs.filter(hotel=hotel)


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------

class MaintenancePhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)
    request = _HotelScopedRequestField()

    class Meta:
        model = MaintenancePhoto
        fields = ['id', 'request', 'image', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class BulkMaintenancePhotoSerializer(serializers.Serializer):
    request = _HotelScopedRequestField()
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
    )

    def create(self, validated_data):
        request_obj = validated_data['request']
        user = self.context['request'].user.staff_profile
        photos = []
        for image in validated_data['images']:
            photo = MaintenancePhoto.objects.create(
                request=request_obj, image=image, uploaded_by=user,
            )
            photos.append(photo)
        return photos


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class MaintenanceCommentSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    request = _HotelScopedRequestField()

    class Meta:
        model = MaintenanceComment
        fields = ['id', 'message', 'request', 'staff', 'created_at']
        read_only_fields = ['id', 'staff', 'created_at']


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    comments = MaintenanceCommentSerializer(many=True, read_only=True)
    photos = MaintenancePhotoSerializer(many=True, read_only=True)
    reported_by = StaffSerializer(read_only=True)
    accepted_by = StaffSerializer(read_only=True)
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': _FOREIGN_ROOM_ERROR,
            'incorrect_type': _FOREIGN_ROOM_ERROR,
        },
    )

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'hotel', 'room', 'location_note', 'title', 'description',
            'reported_by', 'accepted_by', 'status', 'created_at', 'updated_at',
            'comments', 'photos',
        ]
        # Phase 6D.1: status and accepted_by are action-only; generic
        # PATCH must not mutate them. hotel/reported_by stay auto-stamped.
        read_only_fields = [
            'id', 'hotel', 'reported_by', 'accepted_by', 'status',
            'created_at', 'updated_at',
        ]

    def validate_room(self, value):
        if value is None:
            return value
        hotel = _request_hotel(self)
        if hotel is None or value.hotel_id != hotel.id:
            raise serializers.ValidationError(_FOREIGN_ROOM_ERROR)
        return value


class MaintenanceRequestReassignSerializer(serializers.Serializer):
    """
    Payload for POST /requests/{pk}/reassign/.

    Accepts an ``accepted_by`` staff id and validates that the target
    belongs to the acting user's hotel. Missing and foreign targets
    return the same generic error so cross-hotel existence cannot be
    probed.
    """
    accepted_by = serializers.IntegerField()

    def validate_accepted_by(self, value):
        hotel = _request_hotel(self)
        if hotel is None:
            raise serializers.ValidationError(_FOREIGN_STAFF_ERROR)
        try:
            staff = Staff.objects.get(pk=value, hotel_id=hotel.id)
        except Staff.DoesNotExist as exc:
            raise serializers.ValidationError(_FOREIGN_STAFF_ERROR) from exc
        return staff
