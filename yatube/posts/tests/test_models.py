from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(
            username='testuser'
        )
        cls.group = Group.objects.create(
            title='название группы',
            slug='слаг',
            description='описание группы'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            pub_date='дата публикации',
            author=cls.author,
            group=cls.group
        )

    def test_verbose_name(self):
        field_verbose_names = {
            'group': 'group',
            'text': 'текст',
        }
        for value, expected in field_verbose_names.items():
            with self.subTest(value=value):
                self.assertEquals(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        field_help_texts = {
            'group': 'выберите группу',
            'text': 'напишите текст',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEquals(
                    self.post._meta.get_field(value).help_text, expected)

    def test_group(self):
        group = self.group
        expected = self.group.title
        self.assertEqual(expected, str(group))

    def test_post(self):
        post = self.post
        expected = post.text[:15]
        self.assertEqual(expected, str(post))
