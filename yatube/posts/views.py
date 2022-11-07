from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from core.utils import paginate
from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    return render(
        request,
        'posts/index.html',
        {
            'page_obj': paginate(
                request,
                Post.objects.select_related('group', 'author'),
                settings.PAGE_SIZE,
            ),
        },
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(
        request,
        'posts/group_list.html',
        {
            'group': group,
            'page_obj': paginate(
                request,
                group.posts.select_related('group', 'author'),
                settings.PAGE_SIZE,
            ),
        },
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        following = author.following.exists()
        return render(
            request,
            'posts/profile.html',
            {
                'author': author,
                'page_obj': paginate(
                    request,
                    author.posts.select_related('author', 'group'),
                    settings.PAGE_SIZE,
                ),
                'following': following,
            },
        )
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': paginate(
                request,
                author.posts.select_related('author', 'group'),
                settings.PAGE_SIZE,
            ),
        },
    )


def post_detail(request, post_id):
    form = CommentForm()
    post = get_object_or_404(Post, id=post_id)
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': form,
        },
    )


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    if request.user != Post.objects.get(id=post_id).author:
        return redirect('posts:post_detail', post_id)

    post = get_object_or_404(Post, id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
            'is_edit': True,
            'post': post,
        },
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': paginate(
                request,
                Post.objects.filter(author__following__user=request.user),
                settings.PAGE_SIZE,
            ),
        },
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    follow = get_object_or_404(Follow, user_id=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', request.user)
