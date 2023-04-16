from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Post, Group, User
from .forms import PostForm

from core.utils import page_division
from posts import constants

num = constants.POSTS_LIMIT_P_PAGE


def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    context = page_division(post_list, request, num)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by('-pub_date')
    context = {
        'group': group,
    }
    context.update(page_division(post_list, request, num))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).order_by('-pub_date')
    context = {
        'author': author,
    }
    context.update(page_division(post_list, request, num))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
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
        return redirect(reverse('posts:profile', args=[post.author]))
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save()
        return redirect(reverse('posts:post_detail', args=[post_id]))
    context = {
        'post': post,
        'is_edit': is_edit,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)
