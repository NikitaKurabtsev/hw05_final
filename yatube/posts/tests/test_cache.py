from collections import Counter

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='тестовый автор'
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='testslug',
            description='тестовое описание'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            pub_date='дата публикации',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()

    def test_cache(self):
        post_count = Post.objects.count()
        auth_request = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(text='тестовый текст', author=self.user)
        self.assertEqual(Post.objects.count(), post_count + 1)
        new_auth_request = self.authorized_client.get(reverse('posts:index'))
        self.assertCountEqual(auth_request, new_auth_request)
        cache.clear()
        last_auth_request = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(
            Counter(list(new_auth_request)), Counter(list(last_auth_request)))
