from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from core.utils import paginate
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginate(request, posts, settings.POST_AMOUNT)
    return render(
        request,
        'posts/index.html',
        {
            'page_obj': page_obj,
        },
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    page_obj = paginate(request, posts, settings.POST_AMOUNT)
    return render(
        request,
        'posts/group_list.html',
        {
            'group': group,
            'page_obj': page_obj,
        },
    )


@cache_page(20, key_prefix='profile_page')
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group')
    page_obj = paginate(request, posts, settings.POST_AMOUNT)
    following = author.following.exists()
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': page_obj,
            'following': following,
        },
    )


def post_detail(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post)
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': form,
            'comments': comments,
        },
    )


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if request.method != 'POST' or not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

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
    user = Follow.objects.filter(user=request.user)
    posts = Post.objects.filter(
        author_id__in=user.values_list('author_id', flat=True)
    )
    page_obj = paginate(request, posts, settings.POST_AMOUNT, )
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': page_obj,
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user_id=request.user.id, author_id=author.id
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user_id=request.user, author_id=author.id).delete()
    return redirect('posts:follow_index')
