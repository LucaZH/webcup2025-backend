import os
from django.conf import settings
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import CustomUser, DeparturePage, EphemeralReading, Vote
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
    
    def get(self, request):
        queryset = DeparturePage.objects.filter(
            Q(is_public=True)
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
        
        limited_data = queryset.values('id', 'title', 'votes_count', 'tone')
        
        return Response(limited_data)
    
    def post(self, request):
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
    
class VoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):

        departure_page = get_object_or_404(DeparturePage, pk=pk)
        
        existing_vote = Vote.objects.filter(
            departure_page=departure_page,
            user=request.user
        ).first()
        
        if existing_vote:
            return Response(
                {'detail': 'You have already voted on this departure page.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vote = Vote(departure_page=departure_page, user=request.user)
        vote.save()
        
        serializer = DeparturePageSerializer(departure_page, context={'request': request})
        return Response(serializer.data)
    
    def delete(self, request, pk):

        departure_page = get_object_or_404(DeparturePage, pk=pk)
        
        vote = Vote.objects.filter(
            departure_page=departure_page,
            user=request.user
        ).first()
        
        if not vote:
            return Response(
                {'detail': 'You have not voted on this departure page.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vote.delete()
        
        serializer = DeparturePageSerializer(departure_page, context={'request': request})
        return Response(serializer.data)
    

class MistralChatAPI(APIView):

    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        messages = request.data.get('messages', [])
        context = request.data.get('context', '')
        last_message = request.data.get('last_message', '')
        language = request.data.get('language', 'fr')
        
        api_key = os.getenv("HF_API_KEY", getattr(settings, "HF_API_KEY", None))
        
        if not api_key:
            return Response(
                {"error": "Hugging Face API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            prompt = self.format_prompt(messages, context, last_message, language)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            response_text = self.query_huggingface_api(prompt, api_key)
            return Response({"response": response_text})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def format_prompt(self, messages, context, last_message, language):
        system_prompt = {
            'fr': (
                "<s>[INST] <<SYS>>\n"
                "Vous êtes un assistant virtuel expert nommé Lumen. Répondez en français en utilisant exclusivement "
                "le contexte fourni. Si l'information n'est pas dans le contexte, indiquez-le clairement. "
                "Structurez votre réponse avec des éléments sans markdown\n"
                "<</SYS>>\n\n"
                "Contexte pertinent:\n{context}\n\n"
                "Historique de conversation:\n{chat_history}\n\n"
                "Dernière question: {last_message} [/INST]"
            ),
            'en': (
                "<s>[INST] <<SYS>>\n"
                "You are a helpful AI assistant named Lumen. Respond in English using only the provided context. "
                "If the answer isn't in the context, clearly state so. Dont use markdown formatting \n"
                "<</SYS>>\n\n"
                "Relevant context:\n{context}\n\n"
                "Conversation history:\n{chat_history}\n\n"
                "Latest query: {last_message} [/INST]"
            )
        }

        chat_history = ""
        for i, msg in enumerate(messages):
            role = "User" if i % 2 == 0 else "Assistant"
            chat_history += f"{role}: {msg}\n"

        try:
            return system_prompt[language].format(
                context=context,
                chat_history=chat_history.strip(),
                last_message=last_message
            )
        except KeyError:
            raise ValueError(f"Unsupported language: {language}")

    def query_huggingface_api(self, prompt, api_key):
        api_url = "https://router.huggingface.co/together/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "model": "mistralai/Mistral-7B-Instruct-v0.3",
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.Timeout:
            raise Exception("API request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                error_data = e.response.json()
                estimated_time = error_data.get('estimated_time', 30)
                raise Exception(f"Model loading - retry in {estimated_time}s")
            else:
                raise Exception(f"API Error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")