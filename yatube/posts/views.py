from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator
    }
    return render(request, "index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts_group.all()
    paginator = Paginator(group_posts, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'group': group,
        'paginator': paginator,
    }
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
    else:
        return render(request, 'new.html', {'form': form})
    return redirect(reverse('posts:index'))


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    else:
        following = False
    context = {
        'author': author,
        'page': page,
        'paginator': paginator,
        'following': following,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    form = CommentForm()
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    author = post.author
    context = {
        'post': post,
        'author': author,
        'form': form,
        'comments': comments,
    }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('posts:post', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if not form.is_valid():
        return render(request, 'new.html', {'form': form, 'post': post})
    post.save()
    return redirect('posts:post', username=username, post_id=post_id)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, 'misc/404.html', {'path': request.path},
                  status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post', username=username, post_id=post_id)
    return redirect('posts:post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    follow_posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(follow_posts, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator
    }
    # информация о текущем пользователе доступна в переменной request.user
    return render(request, 'follow.html', context)


@login_required
def profile_unfollow(request, username):
    """
    Отписаться от автора
    """
    author = get_object_or_404(User, username=username)
    subscription = request.user.follower.filter(
        author=author, user=request.user
    )
    subscription.delete()
    return redirect('posts:profile', author)


@login_required
def profile_follow(request, username):
    """
    Подписаться на конкретного юзера.
    Подписка не доступна при наличии уже имеющееся подписки и самому на себя.
    """
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)
