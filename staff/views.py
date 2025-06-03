from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from .models import Staff
from .serializers import StaffSerializer, UserSerializer, StaffLoginOutputSerializer, StaffLoginInputSerializer
from rest_framework.decorators import action
from django.urls import reverse
from hotel.models import Hotel
from django.db import transaction



class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        print("Authenticated user:", self.request.user)
        return super().get_queryset()


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        print("Login POST data:", request.data)

        # Validate input explicitly:
        input_serializer = StaffLoginInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            print("Input validation errors:", input_serializer.errors)
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Now proceed with normal token authentication
        response = super().post(request, *args, **kwargs)
        print("Response data from ObtainAuthToken:", response.data)

        token_key = response.data.get('token')
        if not token_key:
            # No token, login failed
            print("Login failed: No token returned")
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        token = Token.objects.get(key=token_key)
        user = token.user
        print("Authenticated user:", user.username, "ID:", user.id)

        staff = Staff.objects.filter(user=user).first()
        print("Staff object:", staff)

        hotel_id = staff.hotel.id if staff and staff.hotel else None
        hotel_name = staff.hotel.name if staff and staff.hotel else None
        hotel_slug = staff.hotel.slug if staff and staff.hotel else None

        print("Hotel ID:", hotel_id)
        print("Hotel Name:", hotel_name)

        data = {
            'token': token.key,
            'username': user.username,
            'hotel_id': hotel_id,
            'hotel_name': hotel_name,
            'hotel_slug': hotel_slug,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }

        output_serializer = StaffLoginOutputSerializer(data=data)
        output_serializer.is_valid(raise_exception=True)
        print("Serialized output data:", output_serializer.data)

        return Response(output_serializer.data)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related('user').all()
    serializer_class = StaffSerializer
  
    
    
    def retrieve(self, request, *args, **kwargs):
        print(f"Retrieve staff with pk={kwargs.get('pk')}")
        return super().retrieve(request, *args, **kwargs)
    
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        hotel_id = request.data.get('hotel')
        if not user_id:
            return Response({'user_id': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'user_id': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if staff already exists for this user
        if hasattr(user, 'staff_profile'):
            return Response({'detail': 'Staff profile for this user already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        if not hotel_id:
            return Response({'hotel': 'Hotel ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            hotel = Hotel.objects.get(id=hotel_id)  # <-- This defines `hotel`
        except Hotel.DoesNotExist:
            return Response({'hotel': 'Hotel not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Extract other staff data from request.data
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        department = request.data.get('department', '')
        role = request.data.get('role', None)
        position = request.data.get('position', None)
        email = request.data.get('email', user.email)
        phone_number = request.data.get('phone_number', None)
        is_active = request.data.get('is_active', True)

        # Create Staff linked to user
        staff = Staff.objects.create(
            user=user,
            hotel=hotel,
            first_name=first_name,
            last_name=last_name,
            department=department,
            role=role,
            position=position,
            email=email,
            phone_number=phone_number,
            is_active=is_active,
        )

        # Optionally update user fields
        is_staff = request.data.get('is_staff')
        is_superuser = request.data.get('is_superuser')

        if is_staff is not None:
            user.is_staff = is_staff
        if is_superuser is not None:
            user.is_superuser = is_superuser

        user.save()

        serializer = self.get_serializer(staff)

        # Generate the URL for the staff detail view
        staff_detail_url = reverse('staff-detail', kwargs={'pk': staff.pk})

        # Include the URL in the response data
        data = serializer.data
        data['url'] = staff_detail_url
        data['id'] = staff.id

        return Response(data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Returns the staff profile for the currently logged-in user.
        """
        try:
            staff = Staff.objects.get(user=request.user)
            serializer = self.get_serializer(staff)
            return Response(serializer.data)
        except Staff.DoesNotExist:
            return Response({'detail': 'Staff profile not found for the current user.'}, status=status.HTTP_404_NOT_FOUND)

class StaffRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        data = request.data

        user_data = data.get('user', {})
        username = user_data.get('username')
        password = user_data.get('password')
        email = user_data.get('email')

        if not username or not password:
            return Response({'error': 'Username and password required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        hotel_id = data.get('hotel')
        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Wrap in a transaction to ensure atomicity
        with transaction.atomic():
            # Create User
            user = User.objects.create_user(username=username, password=password, email=email)
            user.is_staff = True
            user.save()

            # Create Staff Profile linked to User
            staff = Staff.objects.create(
                user=user,
                hotel=hotel,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                department=data.get('department', ''),
                role=data.get('role', ''),
                position=data.get('position', ''),
                email=data.get('email', email),
                phone_number=data.get('phone_number', ''),
                is_active=data.get('is_active', True),
                is_on_duty=data.get('is_on_duty', False),
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'staff_id': staff.id,
            'user_id': user.id,
            'token': token.key,
            'username': user.username,
            'hotel': {'id': hotel.id, 'name': hotel.name},
            'first_name': staff.first_name,
            'last_name': staff.last_name,
            'department': staff.department,
            'role': staff.role,
            'position': staff.position,
            'email': staff.email,
            'phone_number': staff.phone_number,
            'is_active': staff.is_active,
        }, status=status.HTTP_201_CREATED)