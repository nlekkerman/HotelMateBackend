from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Staff, Department, Role, UserProfile,
    RegistrationCode, NavigationItem
)
from hotel.models import Hotel
from .serializers import (
    StaffSerializer, UserSerializer,
    StaffLoginOutputSerializer, StaffLoginInputSerializer,
    RegisterStaffSerializer, DepartmentSerializer, RoleSerializer,
    NavigationItemSerializer, RegistrationCodeSerializer,
)
from rest_framework.decorators import action
from .pusher_utils import (
    trigger_staff_profile_update,
    trigger_registration_update,
    trigger_navigation_permission_update,
    trigger_department_role_update
)

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

        staff = Staff.objects.select_related(
            'department', 'hotel', 'role'
        ).prefetch_related('allowed_navigation_items').get(user=user)

        hotel_id = staff.hotel.id if staff and staff.hotel else None
        hotel_name = staff.hotel.name if staff and staff.hotel else None
        hotel_slug = staff.hotel.slug if staff and staff.hotel else None
        access_level = staff.access_level if staff else None
        
        profile_image_url = None
        if staff and staff.profile_image:
            profile_image_url = str(staff.profile_image)
        
        # Get allowed navigation slugs from database
        allowed_navs = [
            nav.slug for nav in staff.allowed_navigation_items.filter(
                is_active=True
            )
        ]

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


from .permissions_superuser import IsSuperUser

class StaffViewSet(viewsets.ModelViewSet):
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.user or instance.user != request.user:
            return Response(
                {"detail": "You can only update your own staff profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        response = super().update(request, *args, **kwargs)
        
        # Trigger Pusher event for staff profile update
        instance.refresh_from_db()
        trigger_staff_profile_update(
            instance.hotel.slug,
            instance,
            action='updated'
        )
        
        return response

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.user or instance.user != request.user:
            return Response(
                {"detail": "You can only update your own staff profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        response = super().partial_update(request, *args, **kwargs)
        
        # Trigger Pusher event for staff profile update
        instance.refresh_from_db()
        trigger_staff_profile_update(
            instance.hotel.slug,
            instance,
            action='updated'
        )
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hotel_slug = instance.hotel.slug
        staff_id = instance.id
        
        response = super().destroy(request, *args, **kwargs)
        
        # Trigger Pusher event for staff deletion
        trigger_staff_profile_update(
            hotel_slug,
            {
                'id': staff_id,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
            },
            action='deleted'
        )
        
        return response

    serializer_class = StaffSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    permission_classes = [IsSuperUser]

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

        # Only allow authenticated users who belong to this hotel
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            Staff.objects.get(user=user, hotel=hotel)
        except Staff.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "You must be a staff member of this hotel to "
                        "create staff."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Pass hotel to serializer if needed
        serializer = RegisterStaffSerializer(
            data=request.data,
            context={"request": request}
        )
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

        return Response(
            self.get_serializer(staff).data,
            status=status.HTTP_201_CREATED
        )

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
        registration_code_value = data.get('registration_code')
        qr_token_value = data.get('qr_token')

        # Validate required fields
        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=400
            )

        if not registration_code_value:
            return Response(
                {'error': 'Registration code is required.'},
                status=400
            )

        # Validate registration code
        try:
            reg_code = RegistrationCode.objects.get(
                code=registration_code_value
            )

            # Check if registration code is already used
            if reg_code.used_by is not None:
                return Response(
                    {'error': 'This registration code has already been used.'},
                    status=400
                )

            # Validate QR token if the registration code has one
            if reg_code.qr_token:
                # If the code has a token, it MUST be provided and match
                if not qr_token_value:
                    return Response(
                        {
                            'error': (
                                'QR token is required for this '
                                'registration code.'
                            )
                        },
                        status=400
                    )
                
                if reg_code.qr_token != qr_token_value:
                    return Response(
                        {
                            'error': (
                                'Invalid QR token. Please use the QR code '
                                'provided with your registration package.'
                            )
                        },
                        status=400
                    )
            # Else: Backward compatibility - old codes without tokens
            # can still register with just the code

        except RegistrationCode.DoesNotExist:
            return Response(
                {'error': 'Invalid registration code.'},
                status=400
            )

        # Get the hotel using the registration code's hotel_slug
        try:
            hotel = Hotel.objects.get(slug=reg_code.hotel_slug)
        except Hotel.DoesNotExist:
            return Response(
                {'error': 'Hotel not found for this registration code.'},
                status=400
            )

        # Create or get user
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists.'},
                status=400
            )

        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()

        # Create user profile linked to registration code
        UserProfile.objects.create(user=user, registration_code=reg_code)

        # Mark the registration code as used (don't delete yet)
        # Code will be deleted when manager creates the staff profile
        reg_code.used_by = user
        reg_code.used_at = timezone.now()
        reg_code.save()

        # Create authentication token
        token, _ = Token.objects.get_or_create(user=user)

        # Trigger Pusher event for pending registration
        trigger_registration_update(
            hotel.slug,
            {
                'user_id': user.id,
                'username': user.username,
                'registration_code': reg_code.code,
            },
            action='pending'
        )

        return Response({
            'user_id': user.id,
            'username': user.username,
            'token': token.key,
            'registration_code': reg_code.code,
            'hotel_slug': hotel.slug,
            'hotel_name': hotel.name,
            'message': (
                'User created successfully. '
                'Please wait for manager to complete your staff profile.'
            ),
        }, status=201)


class GenerateRegistrationPackageAPIView(APIView):
    """
    Generate or retrieve a registration package for staff onboarding.
    Returns registration code + QR code URL + token.
    Only authenticated staff with proper permissions can access.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Create a new registration code with QR code or retrieve existing one
        """
        hotel_slug = request.data.get('hotel_slug')
        code = request.data.get('code')  # Optional: provide specific code

        if not hotel_slug:
            return Response(
                {'error': 'hotel_slug is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify hotel exists
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response(
                {'error': 'Hotel not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions: user must be staff of this hotel
        try:
            staff = request.user.staff_profile
            if staff.hotel.slug != hotel_slug:
                return Response(
                    {'error': 'You can only create codes for your hotel.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Only staff_admin and super_staff_admin can create codes
            if staff.access_level not in [
                'staff_admin', 'super_staff_admin'
            ]:
                return Response(
                    {
                        'error': (
                            'You do not have permission '
                            'to generate registration codes.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        except Staff.DoesNotExist:
            return Response(
                {
                    'error': (
                        'Only staff members can '
                        'generate registration codes.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Create or get registration code
        if code:
            # Check if code already exists
            if RegistrationCode.objects.filter(code=code).exists():
                return Response(
                    {'error': 'Registration code already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            reg_code = RegistrationCode.objects.create(
                code=code,
                hotel_slug=hotel_slug
            )
        else:
            # Generate random code
            import random
            import string
            code = ''.join(
                random.choices(
                    string.ascii_uppercase + string.digits,
                    k=8
                )
            )
            while RegistrationCode.objects.filter(code=code).exists():
                code = ''.join(
                    random.choices(
                        string.ascii_uppercase + string.digits,
                        k=8
                    )
                )
            reg_code = RegistrationCode.objects.create(
                code=code,
                hotel_slug=hotel_slug
            )

        # Generate QR token and QR code
        reg_code.generate_qr_token()
        qr_code_url = reg_code.generate_qr_code()

        # Return the registration package
        serializer = RegistrationCodeSerializer(reg_code)
        return Response({
            'registration_code': reg_code.code,
            'qr_token': reg_code.qr_token,
            'qr_code_url': qr_code_url,
            'hotel_slug': reg_code.hotel_slug,
            'hotel_name': hotel.name,
            'message': (
                'Registration package created successfully. '
                'Provide both the registration code and QR code '
                'to the new employee.'
            ),
            'package_details': serializer.data
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        """
        List all registration codes for the authenticated user's hotel
        """
        try:
            staff = request.user.staff_profile
            hotel_slug = staff.hotel.slug

            # Filter codes by hotel
            codes = RegistrationCode.objects.filter(
                hotel_slug=hotel_slug
            ).order_by('-created_at')

            serializer = RegistrationCodeSerializer(codes, many=True)
            return Response({
                'hotel_slug': hotel_slug,
                'hotel_name': staff.hotel.name,
                'registration_codes': serializer.data
            }, status=status.HTTP_200_OK)

        except Staff.DoesNotExist:
            return Response(
                {
                    'error': (
                        'Only staff members can '
                        'view registration codes.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )


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

        email_message = f"""
HotelsMates Password Reset Link

Hello {user.username},

You have requested to reset your password for your HotelsMates account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
HotelsMates Team
"""
        
        send_mail(
            subject="HotelsMates - Password Reset Link",
            message=email_message,
            from_email=f"HotelsMates Team <{settings.EMAIL_HOST_USER}>",
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


class PendingRegistrationsAPIView(APIView):
    """
    GET endpoint to fetch users who have registered but don't have
    a Staff profile yet.
    Returns users with their registration codes for manager review.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, hotel_slug):
        # Verify requesting user has access to this hotel
        try:
            requesting_staff = Staff.objects.get(user=request.user)
            if requesting_staff.hotel.slug != hotel_slug:
                return Response(
                    {'error': 'Access denied to this hotel.'},
                    status=403
                )
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Only staff members can access this endpoint.'},
                status=403
            )

        # Get all used registration codes for this hotel
        used_codes = RegistrationCode.objects.filter(
            hotel_slug=hotel_slug,
            used_by__isnull=False
        ).select_related('used_by')

        pending_users = []
        for code in used_codes:
            user = code.used_by
            # Check if user has no staff profile
            if not hasattr(user, 'staff_profile'):
                pending_users.append({
                    'user_id': user.id,
                    'username': user.username,
                    'registration_code': code.code,
                    'registered_at': code.used_at,
                })

        return Response({
            'hotel_slug': hotel_slug,
            'pending_count': len(pending_users),
            'pending_users': pending_users,
        }, status=200)


class CreateStaffFromUserAPIView(APIView):
    """
    POST endpoint to create a Staff profile for a registered user.
    Deletes the registration code after successful staff creation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, hotel_slug):
        # Verify requesting user has manager/admin access
        try:
            requesting_staff = Staff.objects.get(user=request.user)
            if requesting_staff.hotel.slug != hotel_slug:
                return Response(
                    {'error': 'Access denied to this hotel.'},
                    status=403
                )
            # Any staff member of the hotel can create staff (no access_level restriction)
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Only staff members can access this endpoint.'},
                status=403
            )

        # Get data from request
        user_id = request.data.get('user_id')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        email = request.data.get('email', '')
        department_id = request.data.get('department_id')
        role_id = request.data.get('role_id')
        access_level = request.data.get('access_level', 'regular_staff')
        is_active = request.data.get('is_active', True)

        if not user_id:
            return Response(
                {'error': 'user_id is required.'},
                status=400
            )

        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=404
            )

        # Check if staff already exists
        if hasattr(user, 'staff_profile'):
            return Response(
                {'error': 'Staff profile already exists for this user.'},
                status=400
            )

        # Get hotel
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response(
                {'error': 'Hotel not found.'},
                status=404
            )

        # Get department and role if provided
        department = None
        role = None
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                return Response(
                    {'error': 'Department not found.'},
                    status=404
                )

        if role_id:
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                return Response(
                    {'error': 'Role not found.'},
                    status=404
                )

        # Create the staff profile
        staff = Staff.objects.create(
            user=user,
            hotel=hotel,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            role=role,
            access_level=access_level,
            is_active=is_active,
            is_on_duty=False
        )

        # Find and DELETE the registration code
        try:
            reg_code = RegistrationCode.objects.get(
                hotel_slug=hotel_slug,
                used_by=user
            )
            deleted_code = reg_code.code
            reg_code.delete()
        except RegistrationCode.DoesNotExist:
            deleted_code = None  # Code might already be deleted

        # Serialize the created staff
        serializer = StaffSerializer(staff)

        # Trigger Pusher event for new staff profile
        trigger_staff_profile_update(hotel_slug, staff, action='created')
        trigger_registration_update(
            hotel_slug,
            {
                'user_id': user.id,
                'username': user.username,
                'staff_id': staff.id,
                'registration_code': deleted_code,
            },
            action='approved'
        )

        return Response({
            'message': 'Staff profile created successfully.',
            'staff': serializer.data,
            'deleted_code': deleted_code,
        }, status=201)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments.
    List, create, retrieve, update, delete departments.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'id']
    ordering = ['name']


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles.
    List, create, retrieve, update, delete roles.
    Filter by department using ?department_slug=<slug>
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['department', 'department__slug']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'id']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Filter roles by department_slug query parameter.
        """
        queryset = Role.objects.select_related('department').all()
        department_slug = self.request.query_params.get(
            'department_slug', None
        )
        
        if department_slug is not None:
            queryset = queryset.filter(
                department__slug=department_slug
            )
        
        return queryset


class NavigationItemViewSet(viewsets.ModelViewSet):
    """
    Manage Navigation Items (Links).
    - List/Retrieve: Any authenticated user
    - Create/Update/Delete: Only Django superuser (is_superuser=True)
    """
    queryset = NavigationItem.objects.all()
    serializer_class = NavigationItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination
    lookup_field = 'slug'
    
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    search_fields = ['name', 'slug', 'path', 'description']
    ordering_fields = ['display_order', 'name', 'id']
    ordering = ['display_order', 'name']
    
    def get_queryset(self):
        """Filter navigation items by hotel and active status"""
        queryset = NavigationItem.objects.all()
        
        # Filter by hotel slug if provided
        hotel_slug = self.request.query_params.get('hotel_slug', None)
        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)
        
        # Allow filtering by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(
                is_active=is_active.lower() == 'true'
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """Only Django superuser can create navigation items"""
        if not self.request.user.is_superuser:
            raise permissions.PermissionDenied(
                "Only Django superusers can create navigation items."
            )
        serializer.save()
    
    def perform_update(self, serializer):
        """Only Django superuser can update navigation items"""
        if not self.request.user.is_superuser:
            raise permissions.PermissionDenied(
                "Only Django superusers can update navigation items."
            )
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only Django superuser can delete navigation items"""
        if not self.request.user.is_superuser:
            raise permissions.PermissionDenied(
                "Only Django superusers can delete navigation items."
            )
        instance.delete()


class StaffNavigationPermissionsView(APIView):
    """
    Manage staff navigation permissions.
    Only super_staff_admin can assign navigation items to staff.
    
    GET /api/staff/staff/{staff_id}/navigation-permissions/
    PUT /api/staff/staff/{staff_id}/navigation-permissions/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, staff_id):
        """Get navigation permissions for a staff member"""
        staff = get_object_or_404(Staff, id=staff_id)
        
        # Check if requester is super_staff_admin
        requester_staff = get_object_or_404(Staff, user=request.user)
        if requester_staff.access_level != 'super_staff_admin':
            return Response(
                {
                    "detail": "Only Super Staff Admins can view "
                    "navigation permissions."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        navigation_items = staff.allowed_navigation_items.all()
        serializer = NavigationItemSerializer(navigation_items, many=True)
        
        return Response({
            'staff_id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'navigation_items': serializer.data,
            'navigation_item_ids': [item.id for item in navigation_items]
        })
    
    def put(self, request, staff_id):
        """Update navigation permissions for a staff member"""
        staff = get_object_or_404(Staff, id=staff_id)
        
        # Check if requester is super_staff_admin
        requester_staff = get_object_or_404(Staff, user=request.user)
        if requester_staff.access_level != 'super_staff_admin':
            return Response(
                {
                    "detail": "Only Super Staff Admins can update "
                    "navigation permissions."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get navigation item IDs from request
        nav_item_ids = request.data.get('navigation_item_ids', [])
        
        # Validate that all IDs exist
        navigation_items = NavigationItem.objects.filter(
            id__in=nav_item_ids, is_active=True
        )
        
        if len(navigation_items) != len(nav_item_ids):
            return Response(
                {"detail": "Some navigation item IDs are invalid."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the staff's allowed navigation items
        staff.allowed_navigation_items.set(navigation_items)
        
        # Return updated data
        serializer = NavigationItemSerializer(navigation_items, many=True)
        
        # Trigger Pusher event for navigation permission update
        nav_slugs = [item.slug for item in navigation_items]
        trigger_navigation_permission_update(
            staff.hotel.slug,
            staff.id,
            nav_slugs
        )
        
        return Response({
            'staff_id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'message': 'Navigation permissions updated successfully.',
            'navigation_items': serializer.data,
            'navigation_item_ids': [item.id for item in navigation_items]
        })


class SaveFCMTokenView(APIView):
    """
    Save FCM device token for push notifications
    POST: /api/staff/save-fcm-token/
    Body: {"fcm_token": "device_token_here"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            return Response(
                {"error": "FCM token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            staff = Staff.objects.get(user=request.user)
            staff.fcm_token = fcm_token
            staff.save(update_fields=['fcm_token'])
            
            return Response({
                "message": "FCM token saved successfully",
                "staff_id": staff.id,
                "has_fcm_token": True
            }, status=status.HTTP_200_OK)
            
        except Staff.DoesNotExist:
            return Response(
                {"error": "Staff profile not found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )

