from rest_framework import serializers
from .models import CustomUser, DeparturePage, EphemeralReading, Vote
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model

class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        model = get_user_model()
        fields = UserDetailsSerializer.Meta.fields
        read_only_fields = ('email',)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']


class DeparturePageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DeparturePage
        fields = [
            'id', 'user', 'title', 'content', 'design_data', 'template_id',
            'creation_date', 'is_public', 'is_anonymous', 'is_ephemeral',
            'ending_type', 'tone'
        ]
        read_only_fields = ['id', 'user', 'creation_date']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class DeparturePageCreateSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DeparturePage
        fields = [
            'title', 'content', 'design_data', 'template_id',
            'is_public', 'is_anonymous', 'is_ephemeral',
            'ending_type', 'tone', 'votes_count', 'image', 'image_url'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class EphemeralReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EphemeralReading
        fields = ['id', 'departure_page', 'has_been_viewed', 'view_date']
        read_only_fields = ['id', 'has_been_viewed', 'view_date']


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'departure_page', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        departure_page = validated_data.get('departure_page')
        existing_vote = Vote.objects.filter(
            departure_page=departure_page,
            user=user
        ).first()
        
        if existing_vote:
            return existing_vote
            
        return super().create(validated_data)