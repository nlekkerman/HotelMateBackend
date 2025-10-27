from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import Staff, Department, Role, UserProfile, RegistrationCode
from hotel.models import Hotel
from .serializers import (
    StaffSerializer, UserSerializer,
    StaffLoginOutputSerializer, StaffLoginInputSerializer,
    RegisterStaffSerializer,
)
from rest_framework.decorators import action
from .permissions import Permissions

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
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
        return Response(data)

class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optionally filter or log authenticated user
        return super().get_queryset()


class CustomAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
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
        allowed_navs = Permissions.get_accessible_navs(staff)

        # Firebase FCM token handling has been removed

        data = {
            'staff_id': staff.id,
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
            'allowed_navs': allowed_navs,
            'profile_image_url': profile_image_url,
            'role': staff.role.name if staff.role else None,
            'department': staff.department.name if staff.department else None,
        }

        output_serializer = StaffLoginOutputSerializer(data=data, context={'request': request})
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data)


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
        hotel_slug = kwargs.get("hotel_slug")  # get hotel slug from URL
        hotel = get_object_or_404(Hotel, slug=hotel_slug)  # fetch hotel instance

        # Pass hotel to serializer if needed
        serializer = RegisterStaffSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Save staff with hotel assigned
        staff = serializer.save(hotel=hotel)

        # Set user flags if provided
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
        registration_code_value = data.get('registration_code', None)  # optional

        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=400)

        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)

        if registration_code_value:
            try:
                reg_code = RegistrationCode.objects.get(code=registration_code_value)
                profile.registration_code = reg_code
                profile.save()
            except RegistrationCode.DoesNotExist:
                return Response({'error': 'Invalid registration code.'}, status=400)

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user_id': user.id,
            'username': user.username,
            'token': token.key,
            'registration_code': profile.registration_code.code if profile.registration_code else None,
            'created': created,
        }, status=201 if created else 200)


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


class UsersByHotelRegistrationCodeAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            staff = Staff.objects.get(user=user)
            if not staff.hotel:
                return User.objects.none()
            hotel_slug = staff.hotel.slug
        except Staff.DoesNotExist:
            return User.objects.none()

        # Get all registration codes for this hotel
        hotel_codes = RegistrationCode.objects.filter(hotel_slug=hotel_slug)
        hotel_code_values = set(hotel_codes.values_list('code', flat=True))

        users_with_codes = []
        for u in User.objects.all():
            try:
                if u.profile and u.profile.registration_code:
                    code_str = u.profile.registration_code.code
                    if code_str in hotel_code_values:
                        users_with_codes.append(u)
            except UserProfile.DoesNotExist:
                pass  # user has no profile, skip

        return users_with_codes

