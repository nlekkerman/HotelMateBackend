from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import Staff, Department, Role
from .serializers import (
    StaffSerializer, UserSerializer,
    StaffLoginOutputSerializer, StaffLoginInputSerializer,
    RegisterStaffSerializer,
)
from rest_framework.decorators import action

from staff.permissions import IsSameHotelOrAdmin

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
class StaffMetadataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return departments and roles as serialized objects
        departments = Department.objects.all()
        roles = Role.objects.all()
        return Response({
            "departments": [{"id": d.id, "name": d.name, "slug": d.slug} for d in departments],
            "roles": [{"id": r.id, "name": r.name, "slug": r.slug} for r in roles],
            "access_levels": Staff.ACCESS_LEVEL_CHOICES,
        })


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optionally filter or log authenticated user
        return super().get_queryset()


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        input_serializer = StaffLoginInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        response = super().post(request, *args, **kwargs)
        token_key = response.data.get('token')
        if not token_key:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        token = Token.objects.get(key=token_key)
        user = token.user

        staff = Staff.objects.select_related('department', 'hotel', 'role').get(user=user)

        hotel_id = staff.hotel.id if staff and staff.hotel else None
        hotel_name = staff.hotel.name if staff and staff.hotel else None
        hotel_slug = staff.hotel.slug if staff and staff.hotel else None
        access_level = staff.access_level if staff else None
        
        profile_image_url = None
        if staff and staff.profile_image:
            profile_image_url = str(staff.profile_image)

        fcm_token = request.data.get("fcm_token")
        if staff and fcm_token:
            from .models import StaffFCMToken

            StaffFCMToken.objects.filter(token=fcm_token).exclude(staff=staff).delete()
            StaffFCMToken.objects.update_or_create(
                staff=staff,
                token=fcm_token,
                defaults={'staff': staff},
            )

        data = {
            'token': token.key,
            'username': user.username,
            'hotel_id': hotel_id,
            'hotel_name': hotel_name,
            'hotel_slug': hotel_slug,
            'hotel': {
                'id': hotel_id,
                'name': hotel_name,
                'slug': hotel_slug,
            },
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'access_level': access_level,
            'profile_image_url': profile_image_url,
        }

        output_serializer = StaffLoginOutputSerializer(data=data, context={'request': request})
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data)


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]

    # Enable filtering by related fields using __ notation
    filterset_fields = ['department__slug', 'role__slug', 'hotel__slug']
    ordering_fields = ['user__username', 'department__name', 'role__name', 'hotel__name']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        qs = Staff.objects.select_related("user", "hotel", "department", "role")
        user = self.request.user

        if not user.is_authenticated:
            return Staff.objects.none()

        if user.is_superuser:
            return qs

        try:
            my_staff_profile = Staff.objects.get(user=user)
        except Staff.DoesNotExist:
            return Staff.objects.none()

        return qs.filter(hotel=my_staff_profile.hotel)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsSameHotelOrAdmin]
        elif self.action == "create":
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = RegisterStaffSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        staff = serializer.save()

        user = staff.user
        if "is_staff" in request.data:
            user.is_staff = request.data["is_staff"]
        if "is_superuser" in request.data:
            user.is_superuser = request.data["is_superuser"]
        user.save()

        return Response(self.get_serializer(staff).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        try:
            staff = Staff.objects.get(user=request.user)
            serializer = self.get_serializer(staff)
            return Response(serializer.data)
        except Staff.DoesNotExist:
            return Response(
                {"detail": "Staff profile not found for the current user."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"], url_path="by_department", permission_classes=[permissions.IsAuthenticated])
    def by_department(self, request):
        try:
            staff_profile = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response({"detail": "Staff profile not found."}, status=404)

        department_param = request.query_params.get("department")
        if not department_param:
            return Response({"detail": "Department query param is required."}, status=400)

        if department_param.isdigit():
            department = Department.objects.filter(id=int(department_param)).first()
        else:
            department = Department.objects.filter(slug=department_param).first()

        if not department:
            return Response({"detail": "Department not found."}, status=404)

        staff_qs = Staff.objects.filter(hotel=staff_profile.hotel, department=department)
        page = self.paginate_queryset(staff_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(staff_qs, many=True)
        return Response(serializer.data, status=200)

class StaffRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user_id': user.id,
            'username': user.username,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        frontend_base_url = request.data.get("frontend_base_url")

        if not email or not frontend_base_url:
            return Response({"error": "Email and frontend_base_url are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Security: always respond success message
            return Response({"message": "If this email exists, a reset link has been sent."}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{frontend_base_url}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Password Reset Request",
            message=f"Hello {user.username},\n\nClick below to reset your password:\n{reset_url}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return Response({"message": "Password reset link sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("password")

        if not all([uid, token, new_password]):
            return Response({"error": "Missing fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful."})
