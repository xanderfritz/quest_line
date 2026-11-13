import requests

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Article


# save the old approved value before the save so we can tell if it flipped
@receiver(pre_save, sender=Article)
def cache_old_approved(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_approved = old.approved
        except sender.DoesNotExist:
            instance._old_approved = False
    else:
        instance._old_approved = False


# when article gets approved, email subscribers and log to /api/approved/
@receiver(post_save, sender=Article)
def on_article_approved(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_approved', False)
    if instance.approved and not old:
        send_email_to_subscribers(instance)
        post_to_approved_api(instance)


def send_email_to_subscribers(article):
    # grab everyone subbed to this journalist or publisher
    emails = set()
    for u in article.author.reader_fans.all():
        if u.email:
            emails.add(u.email)
    if article.publisher:
        for u in article.publisher.reader_subscribers.all():
            if u.email:
                emails.add(u.email)
    if not emails:
        return
    body = (
        f"a new article has been approved:\n\n"
        f"title: {article.title}\n"
        f"by: {article.author.username}\n"
        f"publisher: {article.publisher.name if article.publisher else 'independent'}\n\n"
        f"{article.content}\n"
    )
    EmailMessage(
        subject=f"new post from the chronicle: {article.title}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(emails),
    ).send(fail_silently=True)


def post_to_approved_api(article):
    # log the approved article to our own api endpoint
    try:
        requests.post(
            settings.APPROVED_ENDPOINT,
            json={
                'id': article.id,
                'title': article.title,
                'author': article.author.username,
                'publisher': article.publisher.name if article.publisher else None,
            },
            timeout=2,
        )
    except Exception:
        # if the request fails dont crash the save
        pass
