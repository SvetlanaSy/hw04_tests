from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User


class PostURLTests(TestCase):
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
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(self.any_user)
        self.authorized_author.force_login(self.user)

    def test_page_url_exists_at_desired_location(self):
        """Страницы доступны пользователю."""
        responses = [
            self.client.get('/'),
            self.authorized_client.get('/'),
            self.authorized_author.get('/'),
            self.client.get(f'/group/{self.group.slug}/'),
            self.authorized_client.get(f'/group/{self.group.slug}/'),
            self.authorized_author.get(f'/group/{self.group.slug}/'),
            self.client.get(f'/profile/{self.user.username}/'),
            self.authorized_client.get(f'/profile/{self.user.username}/'),
            self.authorized_author.get(f'/profile/{self.user.username}/'),
            self.client.get(f'/posts/{self.post.pk}/'),
            self.authorized_client.get(f'/posts/{self.post.pk}/'),
            self.authorized_author.get(f'/posts/{self.post.pk}/'),
            self.authorized_client.get('/create/'),
            self.authorized_author.get('/create/'),
            self.authorized_author.get(f'/posts/{self.post.pk}/edit/')
        ]
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(
                    response.status_code, HTTPStatus.OK)

    def test_pages_url_redirect_improper_clients(self):
        """Страницы по адресам /create/, /edit/перенаправят
        несоответвтвующего пользователя.
        """
        responses = [
            self.client.get('/create/'),
            self.client.get(f'/posts/{self.post.pk}/edit/'),
            self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        ]
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(
                    response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_url(self):
        """Страница /unexisting_page/  не доступна пользователю."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_redirect_unauthorized_on_detail(self):
        """Страница по адресу /edit/ перенаправит
        пользователя на страницу /post_detail/.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            follow=True)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.pk}))

    def test_post_redirect_anonymous_on_admin_login(self):
        """Страницы по адресу /create/,/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        post_address_redirects = {
            reverse('posts:post_create'):
            reverse('users:login') + '?next=' + reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            reverse('users:login') + '?next=' + reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}), }
        for address, redirect in post_address_redirects.items():
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(response, redirect)
