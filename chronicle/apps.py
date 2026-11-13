from django.apps import AppConfig
from django.db.models.signals import post_migrate


# runs after migrate - makes sure the three groups exist with the right perms
def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from .models import Article, Newsletter

    reader, _ = Group.objects.get_or_create(name='Reader')
    editor, _ = Group.objects.get_or_create(name='Editor')
    journalist, _ = Group.objects.get_or_create(name='Journalist')

    def perms_for(model, actions):
        # grab the Permission objects for the given model + action list
        ct = ContentType.objects.get_for_model(model)
        result = []
        for a in actions:
            codename = f'{a}_{model._meta.model_name}'
            result.append(Permission.objects.get(content_type=ct, codename=codename))
        return result

    # reader can only view
    reader.permissions.set(
        perms_for(Article, ['view']) + perms_for(Newsletter, ['view'])
    )
    # editor can view, change, delete
    editor.permissions.set(
        perms_for(Article, ['view', 'change', 'delete'])
        + perms_for(Newsletter, ['view', 'change', 'delete'])
    )
    # journalist can add, view, change, delete
    journalist.permissions.set(
        perms_for(Article, ['add', 'view', 'change', 'delete'])
        + perms_for(Newsletter, ['add', 'view', 'change', 'delete'])
    )


class ChronicleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chronicle'

    def ready(self):
        # hook the group setup into migrate
        post_migrate.connect(create_groups, sender=self)
        # importing signals here makes them register
        from . import signals  # noqa: F401
