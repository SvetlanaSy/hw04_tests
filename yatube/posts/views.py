from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

from core.utils import page_division
from posts import constants

num = constants.POSTS_LIMIT_P_PAGE


def index(request):
    post_list = Post.objects.all()
    context = page_division(post_list, request, num)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
    }
    context.update(page_division(post_list, request, num))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    context = {
        'author': author,
    }
    if request.user.is_authenticated:
        follow = Follow.objects.filter(user=request.user, author=author)
        if follow:
            following = True
        else:
            following = False
        context = {
            'author': author,
            'following': following,
        }
    
    context.update(page_division(post_list, request, num))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse('posts:profile', args=[post.author]))
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect(reverse('posts:post_detail', args=[post_id]))
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        post = form.save()
        return redirect(reverse('posts:post_detail', args=[post_id]))
    context = {
        'post': post,
        'is_edit': is_edit,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


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
    post_list = Post.objects.filter(author__following__user=request.user)
    context = page_division(post_list, request, num)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()
    return redirect('posts:profile', author.username)
