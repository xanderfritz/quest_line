from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Article, Newsletter, Publisher, User


# helper - add a user to a group
def put_in_group(user, name):
    group, _ = Group.objects.get_or_create(name=name)
    user.groups.add(group)


# shared setup - users + publisher + articles reused by most tests
class BaseSetup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.publisher = Publisher.objects.create(name='fantasy press', description='news of the realms')

        cls.reader = User.objects.create_user(
            username='reader1', password='pass12345', email='reader@test.com', role=User.READER,
        )
        put_in_group(cls.reader, 'Reader')

        cls.journalist = User.objects.create_user(
            username='scribe1', password='pass12345', email='scribe@test.com', role=User.JOURNALIST,
        )
        put_in_group(cls.journalist, 'Journalist')

        cls.other_journalist = User.objects.create_user(
            username='scribe2', password='pass12345', email='scribe2@test.com', role=User.JOURNALIST,
        )
        put_in_group(cls.other_journalist, 'Journalist')

        cls.editor = User.objects.create_user(
            username='editor1', password='pass12345', email='editor@test.com', role=User.EDITOR,
        )
        put_in_group(cls.editor, 'Editor')

        # one approved article and one pending, both by the journalist
        cls.approved_article = Article.objects.create(
            title='dragons in the north',
            content='they have returned',
            author=cls.journalist,
            publisher=cls.publisher,
            approved=True,
        )
        cls.pending_article = Article.objects.create(
            title='pending news',
            content='in review',
            author=cls.journalist,
            publisher=cls.publisher,
            approved=False,
        )


# model tests

class ModelTests(BaseSetup):
    def test_user_role_set(self):
        self.assertEqual(self.reader.role, 'reader')
        self.assertEqual(self.journalist.role, 'journalist')
        self.assertEqual(self.editor.role, 'editor')

    def test_non_reader_cannot_keep_subscriptions(self):
        # a reader can have subs
        self.reader.subscriptions_publishers.add(self.publisher)
        self.assertEqual(self.reader.subscriptions_publishers.count(), 1)
        # flipping to journalist should clear them on save
        self.reader.role = User.JOURNALIST
        self.reader.save()
        self.assertEqual(self.reader.subscriptions_publishers.count(), 0)

    def test_newsletter_m2m_articles(self):
        n = Newsletter.objects.create(title='weekly', description='w', author=self.journalist)
        n.articles.add(self.approved_article)
        self.assertIn(self.approved_article, n.articles.all())


# api - anonymous access

class ApiAnonTests(BaseSetup):
    def setUp(self):
        self.client = APIClient()

    def test_anonymous_cannot_list_articles(self):
        r = self.client.get(reverse('api_article_list'))
        self.assertEqual(r.status_code, 401)

    def test_anonymous_cannot_create(self):
        r = self.client.post(reverse('api_article_list'), {'title': 'x', 'content': 'y'})
        self.assertEqual(r.status_code, 401)


# api - token exchange

class ApiTokenTests(BaseSetup):
    def test_token_login_success(self):
        client = APIClient()
        r = client.post(reverse('api_token'), {'username': 'reader1', 'password': 'pass12345'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)

    def test_token_login_failure(self):
        client = APIClient()
        r = client.post(reverse('api_token'), {'username': 'reader1', 'password': 'wrong'})
        self.assertEqual(r.status_code, 400)


# api - role gated access to articles

class ApiArticleAccessTests(BaseSetup):
    # make an authed api client for a user
    def auth_client(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def test_reader_can_list_approved_only(self):
        client = self.auth_client(self.reader)
        r = client.get(reverse('api_article_list'))
        self.assertEqual(r.status_code, 200)
        titles = [a['title'] for a in r.data]
        self.assertIn('dragons in the north', titles)
        self.assertNotIn('pending news', titles)

    def test_reader_cannot_create(self):
        client = self.auth_client(self.reader)
        r = client.post(reverse('api_article_list'), {
            'title': 'reader post',
            'content': 'nope',
            'publisher': self.publisher.id,
        })
        self.assertEqual(r.status_code, 403)

    def test_journalist_can_create(self):
        client = self.auth_client(self.journalist)
        r = client.post(reverse('api_article_list'), {
            'title': 'new quest',
            'content': 'fresh ink',
            'publisher': self.publisher.id,
        })
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Article.objects.filter(title='new quest').exists())

    def test_journalist_cannot_edit_other_journalists_article(self):
        client = self.auth_client(self.other_journalist)
        r = client.put(
            reverse('api_article_detail', args=[self.approved_article.id]),
            {'title': 'hijacked'},
            format='json',
        )
        self.assertEqual(r.status_code, 403)

    def test_editor_can_delete_any_article(self):
        client = self.auth_client(self.editor)
        r = client.delete(reverse('api_article_detail', args=[self.approved_article.id]))
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Article.objects.filter(id=self.approved_article.id).exists())


# api - subscribed feed

class ApiSubscribedTests(BaseSetup):
    def auth_client(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def test_subscribed_returns_only_subscribed(self):
        # reader subs to our publisher
        self.reader.subscriptions_publishers.add(self.publisher)
        # another publisher with an article that should NOT show
        other = Publisher.objects.create(name='other press')
        Article.objects.create(
            title='unrelated',
            content='x',
            author=self.journalist,
            publisher=other,
            approved=True,
        )
        client = self.auth_client(self.reader)
        r = client.get(reverse('api_articles_subscribed'))
        self.assertEqual(r.status_code, 200)
        titles = [a['title'] for a in r.data]
        self.assertIn('dragons in the north', titles)
        self.assertNotIn('unrelated', titles)

    def test_subscribed_empty_when_no_subs(self):
        client = self.auth_client(self.reader)
        r = client.get(reverse('api_articles_subscribed'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, [])


# approval signal - should email subs + hit /api/approved/ on approval

class ApprovalSignalTests(BaseSetup):
    def setUp(self):
        # reader subscribes to the author AND the publisher
        self.reader.subscriptions_journalists.add(self.journalist)
        self.reader.subscriptions_publishers.add(self.publisher)

    @patch('chronicle.signals.requests.post')
    def test_approval_sends_email_and_posts_to_api(self, mock_post):
        article = Article.objects.create(
            title='rise of the dark soul',
            content='the ember flickers',
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )
        mail.outbox = []
        article.approved = True
        article.save()
        # email should have been sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('rise of the dark soul', mail.outbox[0].subject)
        self.assertIn('reader@test.com', mail.outbox[0].to)
        # /api/approved/ should have been POSTed to
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertIn('/api/approved/', args[0])
        self.assertEqual(kwargs['json']['title'], 'rise of the dark soul')

    @patch('chronicle.signals.requests.post')
    def test_no_signal_fired_when_already_approved(self, mock_post):
        # saving an already approved article should NOT fire again
        self.approved_article.title = 'edited'
        mail.outbox = []
        self.approved_article.save()
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(mock_post.called)


# editor view flow

class EditorViewTests(BaseSetup):
    def test_editor_can_access_queue(self):
        self.client.login(username='editor1', password='pass12345')
        r = self.client.get(reverse('editor_queue'))
        self.assertEqual(r.status_code, 200)

    def test_journalist_cannot_access_queue(self):
        self.client.login(username='scribe1', password='pass12345')
        r = self.client.get(reverse('editor_queue'))
        self.assertEqual(r.status_code, 403)

    @patch('chronicle.signals.requests.post')
    def test_approving_via_view_fires_signal(self, mock_post):
        self.client.login(username='editor1', password='pass12345')
        mail.outbox = []
        # reader subs so we can confirm the email
        self.reader.subscriptions_journalists.add(self.journalist)
        r = self.client.get(reverse('article_approve', args=[self.pending_article.id]))
        self.assertEqual(r.status_code, 302)
        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mock_post.called)


# newsletter views

class NewsletterTests(BaseSetup):
    def test_journalist_can_create_newsletter(self):
        self.client.login(username='scribe1', password='pass12345')
        r = self.client.post(reverse('newsletter_create'), {
            'title': 'weekly dispatch',
            'description': 'news of the week',
            'articles': [self.approved_article.id],
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Newsletter.objects.filter(title='weekly dispatch').exists())

    def test_reader_cannot_create_newsletter(self):
        self.client.login(username='reader1', password='pass12345')
        r = self.client.get(reverse('newsletter_create'))
        self.assertEqual(r.status_code, 403)
