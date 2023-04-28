import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


from posts.models import Post, Group, User
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_list = Post.objects.all()
        id_list = []
        for post in post_list:
            id_list.append(self.post.id)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )  
        form_data = {
            'text': 'Созданный пост',
            'group': self.group.id,
            'image': uploaded,
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
        # self.assertEqual(post_created[0].image, form_data['image'])
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text=self.post.text,
                image=self.post.image).exists())

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

    def test_post_pages_show_image_context(self):
        '''Изображение передается в context страниц'''
        addresses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                'username': self.post.author.username})
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                image_object = response.context['page_obj'][0]
                self.assertEqual(image_object.image, self.post.image)

    def test_post_detail_show_image_context(self):
        '''Изображение передается на post_detail'''
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context.get('post').image, self.post.image)
