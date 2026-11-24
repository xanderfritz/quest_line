"""Database models for the chronicle app.

Defines the custom User, Publisher, Article and Newsletter models that
power the quest_line news platform.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with a role field.

    :cvar str role: One of READER, EDITOR or JOURNALIST. Controls what
        the user can do in the app.
    """

    READER = 'reader'
    EDITOR = 'editor'
    JOURNALIST = 'journalist'
    ROLES = [
        (READER, 'Reader'),
        (EDITOR, 'Editor'),
        (JOURNALIST, 'Journalist'),
    ]

    role = models.CharField(max_length=20, choices=ROLES, default=READER)

    # reader subs
    subscriptions_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='reader_subscribers',
    )
    subscriptions_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='reader_fans',
    )

    # journalists use user.articles and user.newsletters (reverse FK)

    def save(self, *args, **kwargs):
        """Save the user. If role is not reader, clear any reader subscriptions.

        :raises django.db.DatabaseError: If the underlying save fails.
        """
        # if not a reader, clear the reader subs
        super().save(*args, **kwargs)
        if self.role != self.READER and self.pk:
            self.subscriptions_publishers.clear()
            self.subscriptions_journalists.clear()


class Publisher(models.Model):
    """A publisher that groups editors and journalists.

    Articles can optionally belong to a publisher. Editors can approve
    their publisher's articles and journalists write for that publisher.
    """

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name='publisher_editor_of',
        limit_choices_to={'role': 'editor'},
    )
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name='publisher_writer_of',
        limit_choices_to={'role': 'journalist'},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """A news article written by a journalist.

    :cvar bool approved: True once an editor (or the independent author)
        has approved the article for publication.
    """

    title = models.CharField(max_length=200)
    content = models.TextField()
    # author is a journalist
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles',
        limit_choices_to={'role': 'journalist'},
    )
    # publisher is optional (independent articles have none)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        related_name='articles',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """A journalist's newsletter that groups multiple articles."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='newsletters',
        limit_choices_to={'role': 'journalist'},
    )
    articles = models.ManyToManyField(Article, blank=True, related_name='newsletters')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
