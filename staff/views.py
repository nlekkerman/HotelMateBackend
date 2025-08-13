from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import Staff, Department, Role
from rest_framework.permissions import AllowAny
from hotel.models import Hotel
from .serializers import (
    StaffSerializer, UserSerializer,
    StaffLoginOutputSerializer, StaffLoginInputSerializer,
    RegisterStaffSerializer, StaffMinimalSerializer,
)
from rest_framework.decorators import action
from .permissions import Permissions

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class StaffMetadataView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get(self, request, hotel_slug=None):
        print(f"Received hotel_slug: {hotel_slug}")

        if hotel_slug:
            departments = Department.objects.all()

            roles = Role.objects.filter(
                staff_members__hotel__slug=hotel_slug
            ).distinct()
        else:
            departments = Department.objects.all()
            roles = Role.objects.all()

        data = {
            "departments": [{"id": d.id, "name": d.name, "slug": d.slug} for d in departments],
            "roles": [{"id": r.id, "name": r.name, "slug": r.slug} for r in roles],
            "access_levels": Staff.ACCESS_LEVEL_CHOICES,
        }
        print("Response data:", data)
        return Response(data)

class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optionally filter or log authenticated user
        return super().get_queryset()


class CustomAuthToken(ObtainAuthToken):
    authentication_classes = []
    permission_classes = [AllowAny]
    print(">>> CustomAuthToken POST reached")
    
    def post(self, request, *args, **kwargs):
        print(">>> CustomAuthToken POST reached", request.data)  # ✅ now triggers on POST

        serializer = StaffLoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request=request, username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=400)

        token, created = Token.objects.get_or_create(user=user)

        # If the user has a Staff profile
        try:
            staff = user.staff
            staff_data = StaffMinimalSerializer(staff, context={'request': request}).data
            access_level = staff.access_level
        except Staff.DoesNotExist:
            staff_data = None
            access_level = None

        output = {
            "username": user.username,
            "token": token.key,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "hotel": staff_data.get('hotel') if staff_data else None,
            "hotel_id": staff_data.get('hotel', {}).get('id') if staff_data else None,
            "hotel_name": staff_data.get('hotel', {}).get('name') if staff_data else None,
            "hotel_slug": staff_data.get('hotel', {}).get('slug') if staff_data else None,
            "access_level": access_level,
            "allowed_navs": staff_data.get('allowed_navs') if staff_data else [],
            "profile_image_url": staff_data.get('profile_image_url') if staff_data else None,
            "role": staff_data.get('role', {}).get('name') if staff_data else None,
            "department": staff_data.get('department', {}).get('name') if staff_data else None,
        }

        return Response(output)

class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]

    filterset_fields = ['department__slug', 'role__slug', 'hotel__slug']
    ordering_fields = ['user__username', 'department__name', 'role__name', 'hotel__name']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        qs = Staff.objects.select_related("user", "hotel", "department", "role")
        user = self.request.user
        hotel_slug = self.kwargs.get('hotel_slug')

        if not user.is_authenticated:
            return Staff.objects.none()

        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)

        return qs

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

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated], url_path='me')
    def me(self, request, hotel_slug=None):
        # Get staff filtered by request.user and hotel_slug
        try:
            staff = Staff.objects.get(user=request.user, hotel__slug=hotel_slug)
        except Staff.DoesNotExist:
            return Response(
                {"detail": "Staff profile not found for the current user and hotel."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(staff)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="by_department",
        permission_classes=[permissions.IsAuthenticated]
    )
    def by_department(self, request, hotel_slug=None):
        """
        Returns staff in the given hotel & department slug.
        URL: /staff/<hotel_slug>/by_department/?department=<slug-or-id>
        """
        department_param = request.query_params.get("department")
        if not department_param:
            return Response({"detail": "Department query param is required."}, status=400)

        # Get department by id or slug
        if department_param.isdigit():
            department = Department.objects.filter(id=int(department_param)).first()
        else:
            department = Department.objects.filter(slug=department_param).first()

        if not department:
            return Response({"detail": "Department not found."}, status=404)

        # Get hotel instance from URL param
        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        # Directly filter staff
        staff_qs = Staff.objects.filter(hotel=hotel, department=department)

        # Paginate & serialize
        page = self.paginate_queryset(staff_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(staff_qs, many=True)
        return Response(serializer.data, status=200)
    
    # New action with hotel_slug param
    @action(
        detail=False,
        methods=["get"],
        url_path=r'by_hotel/(?P<hotel_slug>[^/.]+)',
        permission_classes=[permissions.IsAuthenticated],
    )
    def by_hotel(self, request, hotel_slug=None):
        if not hotel_slug:
            return Response({"detail": "Hotel slug is required."}, status=status.HTTP_400_BAD_REQUEST)

        staff_qs = Staff.objects.filter(hotel__slug=hotel_slug)
        page = self.paginate_queryset(staff_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(staff_qs, many=True)
        return Response(serializer.data)


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
