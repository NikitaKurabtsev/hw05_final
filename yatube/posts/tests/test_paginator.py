from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, User


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='тестовый автор'
        )
        for e in range(14):
            Post.objects.create(
                author=cls.user,
                text=f'текст номер {e}'
            )

    def setUp(self):
        self.guest_client = Client()

    def test_paginator(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)
