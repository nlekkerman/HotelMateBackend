"""
Serializers for Staff Chat Attachments
"""
from rest_framework import serializers
from .models import StaffChatAttachment


class StaffChatAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for file attachments in staff chat messages
    """
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    uploader_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffChatAttachment
        fields = [
            'id',
            'file',
            'file_url',
            'file_name',
            'file_type',
            'file_size',
            'file_size_display',
            'mime_type',
            'thumbnail',
            'thumbnail_url',
            'uploaded_at',
            'uploader_name'
        ]
        read_only_fields = [
            'uploaded_at',
            'file_size',
            'mime_type',
            'file_type'
        ]

    def get_file_url(self, obj):
        """Get absolute URL for file"""
        if obj.file and hasattr(obj.file, 'url'):
            file_url = obj.file.url
            # Cloudinary URLs are already absolute
            if file_url.startswith(('http://', 'https://')):
                return file_url
            # For local storage, build absolute URI
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(file_url)
            return file_url
        return None

    def get_thumbnail_url(self, obj):
        """Get absolute URL for thumbnail"""
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            thumbnail_url = obj.thumbnail.url
            # Cloudinary URLs are already absolute
            if thumbnail_url.startswith(('http://', 'https://')):
                return thumbnail_url
            # For local storage, build absolute URI
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(thumbnail_url)
            return thumbnail_url
        return None

    def get_file_size_display(self, obj):
        """Human-readable file size"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_uploader_name(self, obj):
        """Get name of staff member who uploaded the file"""
        sender = obj.message.sender
        return f"{sender.first_name} {sender.last_name}".strip()


class AttachmentUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading file attachments
    """
    files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        help_text="List of files to upload"
    )
    message_id = serializers.IntegerField(
        required=False,
        help_text="Existing message ID to attach files to"
    )
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional message text if creating new message"
    )
    reply_to = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Message ID this is replying to"
    )

    def validate_files(self, files):
        """Validate uploaded files"""
        if not files:
            raise serializers.ValidationError(
                "At least one file is required"
            )

        # Max 10 files per upload
        if len(files) > 10:
            raise serializers.ValidationError(
                "Maximum 10 files can be uploaded at once"
            )

        # Validate each file
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        ALLOWED_EXTENSIONS = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
            '.pdf',
            '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'
        ]

        for file in files:
            # Check file size
            if file.size > MAX_FILE_SIZE:
                size_mb = file.size / (1024 * 1024)
                raise serializers.ValidationError(
                    f'{file.name}: File too large ({size_mb:.2f}MB, '
                    f'max 50MB)'
                )

            # Check file extension
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise serializers.ValidationError(
                    f'{file.name}: File type "{ext}" not allowed'
                )

        return files
