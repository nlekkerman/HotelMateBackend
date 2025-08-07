from rest_framework import serializers
from .models import HotelInfo, HotelInfoCategory, GoodToKnowEntry
from django.utils.text import slugify
from hotel.models import Hotel
from cloudinary.uploader import upload as cloudinary_upload
from django.core.exceptions import ObjectDoesNotExist

class GoodToKnowEntrySerializer(serializers.ModelSerializer):
    hotel_slug = serializers.SlugField(write_only=True)
    image = serializers.ImageField(required=False)

    class Meta:
        model = GoodToKnowEntry
        fields = [
            "hotel_slug",
            "slug",
            "title",
            "content",
            "image",
            "qr_url",
            "generated_at",
            "extra_info",
            "active",
            "created_at",
        ]
        read_only_fields = ["qr_url", "generated_at", "created_at"]

    def create(self, validated_data):
        hotel_slug = validated_data.pop("hotel_slug")
        hotel = Hotel.objects.get(slug=hotel_slug)
        validated_data["hotel"] = hotel

        # Auto-generate slug from title if not explicitly provided
        if not validated_data.get("slug") and validated_data.get("title"):
            validated_data["slug"] = slugify(validated_data["title"])

        instance = super().create(validated_data)
        instance.generate_qr()
        return instance

   
class HotelInfoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelInfoCategory
        fields = ("slug", "name")
    def create(self, validated_data):
        # Auto-generate slug if not provided
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class HotelInfoSerializer(serializers.ModelSerializer):
    time_range = serializers.SerializerMethodField()

    class Meta:
        model = HotelInfo
        fields = [
            "id",
            "hotel",
            "category",
            "title",
            "description",
            "event_date",
            "event_time",
            "end_time",
            "time_range",  # add formatted time range here
            "image",
            "extra_info",
            "active",
            "created_at",
        ]

    def get_time_range(self, obj):
        return obj.time_range_display()

class HotelInfoCreateSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)
    hotel_slug = serializers.SlugField(write_only=True)
    image = serializers.ImageField(required=False)

    class Meta:
        model = HotelInfo
        fields = ["hotel_slug", "category_name", "title", "description", "event_date", "event_time", "image", "end_time"]

    def validate(self, data):
        event_time = data.get('event_time')
        end_time = data.get('end_time')
        if event_time and end_time and end_time <= event_time:
            raise serializers.ValidationError({
                'end_time': "end_time must be after event_time."
            })
        return data

    def create(self, validated_data):
        category_name = validated_data.pop("category_name")
        hotel_slug = validated_data.pop("hotel_slug")
        image_file = validated_data.pop("image", None)

        hotel = Hotel.objects.get(slug=hotel_slug)
        category, created = HotelInfoCategory.objects.get_or_create(name=category_name)

        if image_file:
            validated_data['image'] = image_file

        validated_data["hotel"] = hotel
        validated_data["category"] = category

        return super().create(validated_data)
class HotelInfoUpdateSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True, required=False)
    hotel_slug = serializers.SlugField(write_only=True, required=False)
    image = serializers.ImageField(required=False)

    class Meta:
        model = HotelInfo
        fields = [
            "hotel_slug",
            "category_name",
            "title",
            "description",
            "event_date",
            "event_time",
            "end_time",
            "image",
            "active",
            "extra_info",
        ]

    def validate(self, data):
        event_time = data.get('event_time')
        end_time = data.get('end_time')
        if event_time and end_time and end_time <= event_time:
            raise serializers.ValidationError({
                'end_time': "end_time must be after event_time."
            })
        return data

    def update(self, instance, validated_data):
        category_name = validated_data.pop("category_name", None)
        hotel_slug = validated_data.pop("hotel_slug", None)

        if category_name:
            category, created = HotelInfoCategory.objects.get_or_create(name=category_name)
            instance.category = category

        if hotel_slug:
            hotel = Hotel.objects.get(slug=hotel_slug)
            instance.hotel = hotel

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
