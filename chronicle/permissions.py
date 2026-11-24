"""Permission classes for the chronicle API.

ArticlePermission enforces the role-based rules on the article endpoints.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def in_group(user, name):
    """Check if a user belongs to the named group.

    :param user: The user to check.
    :param str name: The group name.
    :returns: True if the user is authenticated and in the group.
    :rtype: bool
    """
    return user.is_authenticated and user.groups.filter(name=name).exists()


class ArticlePermission(BasePermission):
    """Role-based permission for article endpoints.

    - GET: any authenticated user
    - POST: journalists only
    - PUT / DELETE: editors on any article, journalists only on their own
    """


    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'POST':
            return in_group(request.user, 'Journalist')
        # PUT / PATCH / DELETE
        return in_group(request.user, 'Editor') or in_group(request.user, 'Journalist')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if in_group(request.user, 'Editor'):
            return True
        # journalists can only edit their own
        return obj.author_id == request.user.id
