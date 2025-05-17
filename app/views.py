from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import CustomUser, DeparturePage, EphemeralReading
from .serializers import (
    CustomUserDetailsSerializer, DeparturePageSerializer, DeparturePageCreateSerializer
)
from .permissions import IsOwnerOrReadOnly


class UserListView(ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserDetailView(RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get the current authenticated user"""
        serializer = CustomUserDetailsSerializer(request.user)
        return Response(serializer.data)


class DeparturePageListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        user = request.user
        queryset = DeparturePage.objects.filter(
            Q(user=user) | (Q(is_public=True) & ~Q(user=user))
        )
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(ending_type__icontains=search) |
                Q(tone__icontains=search)
            )
        
        ordering = request.query_params.get('ordering')
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-creation_date')
            
        serializer = DeparturePageSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new departure page"""
        serializer = DeparturePageCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            full_serializer = DeparturePageSerializer(serializer.instance)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeparturePageDetailView(APIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_object(self, pk):
        """Get the departure page object"""
        page = get_object_or_404(DeparturePage, pk=pk)
        self.check_object_permissions(self.request, page)
        return page
    
    def get(self, request, pk):
        page = self.get_object(pk)
        serializer = DeparturePageSerializer(page)
        return Response(serializer.data)
    
    def put(self, request, pk):
        page = self.get_object(pk)
        serializer = DeparturePageSerializer(page, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        page = self.get_object(pk)
        serializer = DeparturePageSerializer(page, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        page = self.get_object(pk)
        page.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeparturePagePublishView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def post(self, request, pk):
        page = get_object_or_404(DeparturePage, pk=pk)
        self.check_object_permissions(request, page)
        
        page.is_public = True
        page.save()
        return Response({'status': 'page published'})


class DeparturePageShareView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def post(self, request, pk):
        page = get_object_or_404(DeparturePage, pk=pk)
        self.check_object_permissions(request, page)

        share_url = request.build_absolute_uri(f'/api/pages/{page.id}/')
        
        return Response({
            'status': 'page shared',
            'share_url': share_url
        })


class DeparturePageViewReadingView(APIView):

    permission_classes = [permissions.AllowAny]  # Allow anonymous access
    
    def get(self, request, pk):
        page = get_object_or_404(DeparturePage, pk=pk)
        ip_address = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
        print(f"{ip_address} ooo")
        if request.user.is_authenticated:
            user = request.user
            
            reading, created = EphemeralReading.objects.get_or_create(
                departure_page=page,
                viewer=user,
                defaults={'has_been_viewed': False}
            )
            
            if reading.has_been_viewed:
                return Response({
                    'error': 'This page has already been viewed and cannot be viewed again'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            ip_address = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
            print(ip_address)
            reading, created = EphemeralReading.objects.get_or_create(
                departure_page=page,
                viewer=None,
                viewer_ip=ip_address,
                defaults={'has_been_viewed': False}
            )
            
            if reading.has_been_viewed:
                return Response({
                    'error': 'This page has already been viewed and cannot be viewed again'
                }, status=status.HTTP_403_FORBIDDEN)
        
        reading.has_been_viewed = True
        reading.view_date = timezone.now()
        reading.save()
        
        serializer = DeparturePageSerializer(page)
        return Response(serializer.data)