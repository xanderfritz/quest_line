"""REST API endpoints for the chronicle app.

Token authenticated endpoints for listing, creating, updating and
deleting articles, plus the subscribed-articles feed and the
approved-article webhook.
"""

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Article
from .permissions import ArticlePermission
from .serializers import ArticleSerializer


@api_view(['GET', 'POST'])
@permission_classes([ArticlePermission])
def api_article_list(request):
    """List approved articles (GET) or create a new article (POST, journalists only).

    :returns: JSON response with articles list or the created article.
    :rtype: rest_framework.response.Response
    """

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


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ArticlePermission])
def api_article_detail(request, pk):
    """Get, update or delete a single article by primary key.

    :param int pk: Primary key of the article.
    :returns: The article, the updated article, or 204 on delete.
    :rtype: rest_framework.response.Response
    """

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_articles_subscribed(request):
    """Return approved articles from publishers and journalists the reader follows.

    :returns: JSON list of articles.
    :rtype: rest_framework.response.Response
    """

    user = request.user
    pub_ids = user.subscriptions_publishers.values_list('id', flat=True)
    jour_ids = user.subscriptions_journalists.values_list('id', flat=True)
    articles = Article.objects.filter(approved=True).filter(
        Q(publisher_id__in=pub_ids) | Q(author_id__in=jour_ids)
    ).distinct()
    return Response(ArticleSerializer(articles, many=True).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_approved_log(request):
    """Internal webhook that logs approved articles posted by the signal handler.

    :returns: JSON echo of the received data.
    :rtype: rest_framework.response.Response
    """

    print('[api/approved]', request.data)
    return Response({'logged': True, 'data': request.data}, status=status.HTTP_200_OK)
