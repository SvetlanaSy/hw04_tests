from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group
from posts.constants import POSTS_FOR_PAGE_TEST as pages_num
from posts.constants import POSTS_LIMIT_P_PAGE as num

User = get_user_model()


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
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
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
        group_text_0 = first_object.text
        group_0 = first_object.group
        group_author_0 = first_object.author
        group_post_id_0 = first_object.id
        self.assertEqual(group_post_id_0, self.post.id)
        self.assertEqual(group_text_0, self.post.text)
        self.assertEqual(group_0, self.group)
        self.assertEqual(group_author_0, self.post.author)

    def test_profile_page_show_correct_context(self):
        """Шаблон posts_group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        first_object = response.context['page_obj'][0]
        profile_author_0 = first_object.author
        profile_text_0 = first_object.text
        profile_group_0 = first_object.group
        profile_post_id_0 = first_object.id
        self.assertEqual(profile_post_id_0, self.post.id)
        self.assertEqual(profile_group_0, self.group)
        self.assertEqual(profile_text_0, self.post.text)
        self.assertEqual(profile_author_0, self.user)

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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,)
        for post_example in range(pages_num):
            Post.objects.create(
                text=f'text{post_example}',
                author=cls.user, group=cls.group)

    def test_first_page_contains_ten_records(self):
        '''Количество постов на первой странице равно 10'''
        page_responses = [self.client.get(reverse('posts:index')),
                          self.client.get(reverse(
                              'posts:group_list', kwargs={
                                  'slug': 'test-slug'})),
                          self.client.get(reverse(
                              'posts:profile', kwargs={
                                  'username': self.post.author}))]
        for response in page_responses:
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']), num)

    def test_second_page_contains_four_records(self):
        '''Количество постов на второй странице должно быть 4'''
        page_responses = [self.client.get(
                          reverse('posts:index') + '?page=2'),
                          self.client.get(reverse(
                              'posts:group_list', kwargs={
                                  'slug': 'test-slug'}) + '?page=2'),
                          self.client.get(reverse(
                              'posts:profile', kwargs={
                                  'username': self.post.author}) + '?page=2')]
        for response in page_responses:
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']), 4)
