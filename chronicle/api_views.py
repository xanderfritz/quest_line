from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Article
from .permissions import ArticlePermission
from .serializers import ArticleSerializer


# GET lists approved articles, POST lets a journalist make one
@api_view(['GET', 'POST'])
@permission_classes([ArticlePermission])
def api_article_list(request):
    if request.method == 'GET':
        articles = Article.objects.filter(approved=True)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)
    # POST
    serializer = ArticleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# get, update or delete one article
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ArticlePermission])
def api_article_detail(request, pk):
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

    # check object level perms (only editor or the author can edit/delete)
    perm = ArticlePermission()
    if not perm.has_object_permission(request, None, article):
        return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(ArticleSerializer(article).data)
    if request.method == 'PUT':
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # DELETE
    article.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# articles from the readers subbed publishers and journalists
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_articles_subscribed(request):
    user = request.user
    pub_ids = user.subscriptions_publishers.values_list('id', flat=True)
    jour_ids = user.subscriptions_journalists.values_list('id', flat=True)
    articles = Article.objects.filter(approved=True).filter(
        Q(publisher_id__in=pub_ids) | Q(author_id__in=jour_ids)
    ).distinct()
    return Response(ArticleSerializer(articles, many=True).data)


# the signal posts here after an article gets approved
@api_view(['POST'])
@permission_classes([AllowAny])
def api_approved_log(request):
    print('[api/approved]', request.data)
    return Response({'logged': True, 'data': request.data}, status=status.HTTP_200_OK)
