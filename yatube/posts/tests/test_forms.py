import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем временную папку для медиа-файлов;
        # на момент теста медиа папка будет перопределена
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.user = User.objects.create_user(
            username='тестовый автор'
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='testslug',
            description='тестовое описание'
        )
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test.gif',
            content=test_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            pub_date='дата публикации',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.form = PostForm()
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        # Модуль shutil - библиотека Python с прекрасными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок|файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.title,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        # Убедимся, что запись в базе данных не создалась:
        # сравним количество записей до и после отправки формы
        latest = Post.objects.latest('pub_date')
        latest.refresh_from_db()
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(latest.text, form_data['text'])
        self.assertEqual(latest.group.title, form_data['group'])
        self.assertEqual(latest.image, form_data['image'])

    def test_post_edit(self):
        post_count = Post.objects.count()
        post = self.post
        form_data = {
            'text': 'Измененный пост',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[post.author, post.id]),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.group.id, self.post.group.id)

    def test_add_comment(self):
        comment = Comment.objects.create(
            author=self.user,
            post=self.post,
            text='тестовый комментарий'
        )
        comment_count = Comment.objects.count()
        form_data = {
            'text': comment.text,
        }
        self.authorized_client.post(reverse(
            'posts:add_comment',
            args=[self.post.author, self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(Comment.objects.first().text, comment.text)
