from rest_framework import serializers
from .models import Article, Newsletter, Publisher, User


# DRF serializers - turn models into json and back

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description']


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'publisher', 'approved', 'created_at']
        # these are set by the server not by the client
        read_only_fields = ['approved', 'created_at', 'author']


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'description', 'author', 'articles', 'created_at']
        read_only_fields = ['created_at', 'author']
