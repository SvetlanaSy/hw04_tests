from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, User, Comment, Follow
from posts.constants import POSTS_FOR_PAGE_TEST as PAGES_NUM
from posts.constants import POSTS_LIMIT_P_PAGE as NUM


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.any_user = User.objects.create_user(username='AnyUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.post.author.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_page_show_correct_context(self):
        """Шаблон posts_index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_id_0 = first_object.id
        post_group_0 = first_object.group
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_id_0, self.post.id)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон posts_group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        group_object = response.context['group']
        object_context = {
            first_object.text: self.post.text,
            first_object.group: self.group,
            first_object.author: self.post.author,
            first_object.id: self.post.id,
            group_object.title: self.group.title,
            group_object.slug: self.group.slug,
            group_object.description: self.group.description,
            group_object.id: self.group.id, }
        for object, value in object_context.items():
            with self.subTest(object=object):
                self.assertEqual(object, value)

    def test_profile_page_show_correct_context(self):
        """Шаблон posts_profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        first_object = response.context['page_obj'][0]
        author_object = response.context['author']
        object_context = {
            first_object.author: self.user,
            first_object.text: self.post.text,
            first_object.group: self.group,
            first_object.id: self.post.id,
            author_object.id: self.user.id, }
        for object, value in object_context.items():
            with self.subTest(object=object):
                self.assertEqual(object, value)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post.pk})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.user)
        self.assertEqual(
            response.context.get('post').group.slug, self.group.slug)
        self.assertEqual(response.context.get('post').id, self.post.id)

    def test_create_post_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').author, self.user)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post_new = Post.objects.create(
            text='New post',
            author=self.user,
            group=self.group,
        )
        address_list = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author})]
        for address in address_list:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(post_new, response.context['page_obj'][0])

    def test_post_added_correct_group(self):
        """Пост при создании добавлен в нужную группу """
        group_2 = Group.objects.create(
            title='Second group',
            slug='test_slug_2',
            description='Тестовое описание',
        )
        response_group_2 = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{group_2.slug}'}))
        group_2 = response_group_2.context['page_obj']
        self.assertNotIn(self.post, group_2)

    def test_index_page_cache(self):
        response = self.client.get(reverse('posts:index'))
        post_cont = response.content
        new_post = Post.objects.create(
            text='New post',
            author=self.user,)
        response = self.client.get(reverse('posts:index'))
        new_post = response.content
        self.assertEqual(post_cont, new_post)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        post_cache = response.content
        self.assertNotEqual(new_post, post_cache)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(PAGES_NUM):
            cls.post = Post.objects.create(
                text=f'text{i}',
                author=cls.user, group=cls.group)

    def test_first_page_contains_ten_records(self):
        '''Количество постов на первой странице равно 10'''
        page_responses = [self.client.get(reverse('posts:index')),
                          self.client.get(reverse(
                              'posts:group_list', kwargs={
                                  'slug': self.group.slug})),
                          self.client.get(reverse(
                              'posts:profile', kwargs={
                                  'username': self.post.author}))]
        for response in page_responses:
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']), NUM)

    def test_second_page_contains_three_records(self):
        '''Количество постов на второй странице должно быть 3'''
        page_responses = [self.client.get(
                          reverse('posts:index') + '?page=2'),
                          self.client.get(reverse(
                              'posts:group_list', kwargs={
                                  'slug': self.group.slug}) + '?page=2'),
                          self.client.get(reverse(
                              'posts:profile', kwargs={
                                  'username': self.post.author}) + '?page=2')]
        for response in page_responses:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']), PAGES_NUM - NUM)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.any_user = User.objects.create_user(username='AnyUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.any_user,
            text='Тестовый комментарий',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.any_user)

    def test_comment_added_correctly(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post.pk}))
        first_object = response.context['comments'][0]
        self.assertEqual(first_object.post, self.comment.post)
        self.assertEqual(first_object.text, self.comment.text)
        self.assertEqual(first_object.author, self.comment.author)
        self.assertEqual(first_object.id, self.comment.id)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='User')
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Just post',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author.force_login(self.author)

    def test_authorized_client_follow(self):
        '''Авторизованный пользователь может подписываться'''
        follow_count = Follow.objects.count()
        follow_data = {
            'user': self.user,
            'author': self.author,
        }
        self.authorized_client.post(
            reverse('posts:profile_follow', args={self.author.username}),
            data=follow_data,
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            author=self.author,
            user=self.user).exists())

    def test_authorized_client_unfollow(self):
        '''Авторизованный пользователь может отподписываться'''
        follow_count = Follow.objects.count()
        follow_data = {
            'user': self.user,
            'author': self.author,
        }
        self.authorized_client.post(
            reverse('posts:profile_unfollow', args={self.author.username}),
            data=follow_data,
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_post_in_follow_list_follower(self):
        '''Запись появляется в ленте follower'''
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'])

    def test_post_not_in_follow_list_unfollower(self):
        '''Запись не появляется в ленте unfollower'''
        response = self.authorized_author.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])
