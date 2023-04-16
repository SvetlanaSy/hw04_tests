from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User
from posts.forms import PostForm


class PostCreateFormTests(TestCase):
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
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_list = Post.objects.all()
        id_list = []
        for post in post_list:
            id_list.append(self.post.id)
        form_data = {
            'text': 'Созданный пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_created = Post.objects.exclude(id__in=id_list)
        self.assertRedirects(response, reverse('posts:profile',
                             args=[self.post.author]))
        self.assertEqual(post_created.count(), 1)
        self.assertEqual(post_created[0].text, form_data['text'])
        self.assertEqual(post_created[0].group.id, form_data['group'])
        self.assertEqual(post_created[0].author, self.user)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        self.group_2 = Group.objects.create(
            title='Second group',
            slug='test_slug_2',
            description='Тестовое описание',
        )
        posts_count = Post.objects.count()
        form_edit = {
            'text': 'Редактированный текст',
            'group': self.group_2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_edit,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post.id)
        self.assertEqual(post_edit.text, form_edit['text'])
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
                                               'post_id': self.post.pk}))
        self.assertEqual(post_edit.group.id, form_edit['group'])
        self.assertEqual(post_edit.author, self.user)
