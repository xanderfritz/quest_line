from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ArticleForm, NewsletterForm, RegisterForm
from .models import Article, Newsletter, Publisher, User


# helper - check if a user is in a given group
def in_group(user, name):
    return user.is_authenticated and user.groups.filter(name=name).exists()


# public pages

def home(request):
    articles = Article.objects.filter(approved=True).order_by('-created_at')[:12]
    return render(request, 'chronicle/home.html', {'articles': articles})


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    # only editors or the author can see an unapproved article
    if not article.approved:
        is_editor = in_group(request.user, 'Editor')
        is_author = request.user.is_authenticated and article.author_id == request.user.id
        if not is_editor and not is_author:
            return HttpResponseForbidden('not approved yet')
    return render(request, 'chronicle/article_detail.html', {'article': article})


def newsletter_list(request):
    newsletters = Newsletter.objects.order_by('-created_at')
    return render(request, 'chronicle/newsletter_list.html', {'newsletters': newsletters})


def newsletter_detail(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, 'chronicle/newsletter_detail.html', {'newsletter': newsletter})


# auth

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data['role']
            user.save()
            # add the user to the matching group (Reader / Editor / Journalist)
            group_name = user.role.capitalize()
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            login(request, user)
            messages.success(request, f'welcome {user.username}')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'chronicle/register.html', {'form': form})


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        error = 'wrong username or password'
    return render(request, 'chronicle/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('home')


# journalist pages

@login_required
def article_create(request):
    if not in_group(request.user, 'Journalist'):
        return HttpResponseForbidden('journalists only')
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            return redirect('my_articles')
    else:
        form = ArticleForm()
    return render(request, 'chronicle/article_form.html', {'form': form})


@login_required
def my_articles(request):
    if not in_group(request.user, 'Journalist'):
        return HttpResponseForbidden('journalists only')
    articles = Article.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'chronicle/my_articles.html', {'articles': articles})


@login_required
def newsletter_create(request):
    if not in_group(request.user, 'Journalist'):
        return HttpResponseForbidden('journalists only')
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            n = form.save(commit=False)
            n.author = request.user
            n.save()
            form.save_m2m()
            return redirect('newsletter_list')
    else:
        form = NewsletterForm()
    return render(request, 'chronicle/newsletter_form.html', {'form': form})


# editor pages

@login_required
def editor_queue(request):
    if not in_group(request.user, 'Editor'):
        return HttpResponseForbidden('editors only')
    pending = Article.objects.filter(approved=False).order_by('-created_at')
    return render(request, 'chronicle/editor_queue.html', {'articles': pending})


@login_required
def article_approve(request, pk):
    if not in_group(request.user, 'Editor'):
        return HttpResponseForbidden('editors only')
    article = get_object_or_404(Article, pk=pk)
    article.approved = True
    # saving triggers the post_save signal which emails subs + hits /api/approved/
    article.save()
    messages.success(request, f'approved: {article.title}')
    return redirect('editor_queue')


@login_required
def article_delete(request, pk):
    if not in_group(request.user, 'Editor'):
        return HttpResponseForbidden('editors only')
    article = get_object_or_404(Article, pk=pk)
    article.delete()
    return redirect('editor_queue')


# reader subscriptions

@login_required
def subscriptions(request):
    if not in_group(request.user, 'Reader'):
        return HttpResponseForbidden('readers only')
    publishers = Publisher.objects.all()
    journalists = User.objects.filter(role='journalist')
    if request.method == 'POST':
        pub_ids = request.POST.getlist('publishers')
        jour_ids = request.POST.getlist('journalists')
        request.user.subscriptions_publishers.set(pub_ids)
        request.user.subscriptions_journalists.set(jour_ids)
        messages.success(request, 'subscriptions updated')
        return redirect('subscriptions')
    return render(request, 'chronicle/subscriptions.html', {
        'publishers': publishers,
        'journalists': journalists,
        'my_pubs': list(request.user.subscriptions_publishers.values_list('id', flat=True)),
        'my_jours': list(request.user.subscriptions_journalists.values_list('id', flat=True)),
    })
