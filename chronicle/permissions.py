from rest_framework.permissions import BasePermission, SAFE_METHODS


# helper - is this user in the named group
def in_group(user, name):
    return user.is_authenticated and user.groups.filter(name=name).exists()


# api permission for articles
# GET: any logged in user
# POST: journalist only
# PUT / DELETE: editors any, journalists only their own
class ArticlePermission(BasePermission):
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
