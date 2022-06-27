from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='название группы',
            slug='testslug',
            description='описание группы'
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = get_user_model().objects.create_user(username='Nikita')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_any_user(self):
        status_user_urls = {
            '/': 200,
            f'/group/{self.group.slug}/': 200,
            '/new/': 302,
            '/about/author/': 200,
            '/about/tech/': 200,
            '/not_exists/': 404,
        }
        for url, result in status_user_urls.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, result)

    def test_authorized_user(self):
        status_user_urls = {
            '/': 200,
            f'/group/{self.group.slug}/': 200,
            '/new/': 200,
            '/not_exists/': 404,
        }
        for url, result in status_user_urls.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, result)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'index.html',
            f'/group/{self.group.slug}/': 'group.html',
            '/new/': 'new.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
