from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='тестовый автор')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='testslug',
            description='тестовое описание'
        )
        cls.group_wrong = Group.objects.create(
            title='тестовая группа2',
            slug='testslug-wrong',
            description='тестовое описание2'
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
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='тестовый коммент'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(GroupURLTests.user)

    def test_follower_can_see_following_author_posts(self):
        # создаём юзера и подписчика
        author = self.user
        subscriber = User.objects.create_user(
            username='Bob',
            password=12345
        )
        nonsub = User.objects.create_user(
            username='Jack',
            password=12345
        )
        # создаём подписку и пост автора
        Follow.objects.create(user=subscriber, author=author)
        post = Post.objects.create(text='текст', author=author)
        # авторизируем подписчика
        subscriber_client = Client()
        subscriber_client.force_login(subscriber)
        nonfollowed_sub = Client()
        nonfollowed_sub.force_login(nonsub)
        # проверяем ленту
        response = subscriber_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page'])
        response = nonfollowed_sub.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page'])

    def test_subscribe(self):
        # Создаём юзера в бд
        follower = User.objects.create_user(
            username='Andrey',
            password='12345'
        )
        # Эмулируем и авторизируем клиента
        follower_client = Client()
        follower_client.force_login(follower)
        # Присваеваем переменной обращение к follow view
        url_follow = reverse('posts:profile_follow',
                             kwargs={'username': self.user.username})
        # Проверяем есть ли подписка
        follower_client.get(path=url_follow, follow=True)
        self.assertTrue(Follow.objects.filter(user=follower,
                                              author=self.user).exists())

    def test_unsubscribe(self):
        follower = User.objects.create_user(
            username='Andrey',
            password='12345'
        )
        follower_client = Client()
        follower_client.force_login(follower)
        url_unfollow = reverse('posts:profile_unfollow',
                               kwargs={'username': self.user.username})
        follower_client.get(path=url_unfollow, follow=True)
        self.assertFalse(Follow.objects.filter(author=self.user,
                                               user=follower).exists())

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: name"
        templates_pages_names = {
            'index.html': reverse('posts:index'),
            'group.html': (
                reverse('posts:group_posts',
                        kwargs={'slug': f'{self.group.slug}'})
            ),
            'new.html': reverse('posts:new_post'),
        }
        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_form_correct_context(self):
        """Поля формы создания нового поста передают нужные контексты"""
        response = self.authorized_client.get(reverse("posts:new_post"))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field_name, field_format in form_fields.items():
            with self.subTest(value=field_name):
                form_field = (
                    response.context.get('form').fields.get(field_name)
                )
                self.assertIsInstance(form_field, field_format)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом и картинкой"""
        response = self.authorized_client.get(reverse('posts:index'))
        get_page = response.context.get('page')[0]
        image = response.context.get('page')[0].image
        post_text_0 = get_page.text
        post_author_0 = get_page.author
        post_group_0 = get_page.group
        self.assertEqual(post_text_0, 'тестовый текст')
        self.assertEqual(post_author_0.username, 'тестовый автор')
        self.assertEqual(post_group_0.title, 'тестовая группа')
        self.assertEqual(image, self.post.image)

    def test_group_page_show_correct_context(self):
        """
        Шаблон group_posts сформирован с правильным контекстом и картинкой
        """
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': f'{self.group.slug}'})
        )
        image = response.context.get('page')[0].image
        self.assertEqual(response.context.get('group').title,
                         'тестовая группа')
        self.assertEqual(response.context.get('group').description,
                         'тестовое описание')
        self.assertEqual(response.context.get('group').slug, 'testslug')
        self.assertEqual(image, self.post.image)

    def test_new_post_show_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('page')[0], self.post)

    def test_post_group_page(self):
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': f'{self.group.slug}'})
        )
        self.assertEqual(response.context.get('page')[0], self.post)

    def test_post_in_right_group(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={
                'slug': f'{self.group_wrong.slug}'
            }))
        self.assertEqual(response.context.get('group'), self.group_wrong)
        self.assertEqual(len(response.context.get('page').object_list), 0)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом и картинкой"""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user})
        )
        image = response.context.get('page')[0].image
        author = response.context.get('author')
        self.assertEqual(author, self.user)
        self.assertEqual(image, self.post.image)

    def test_post_view_page(self):
        response = self.guest_client.get(reverse(
            'posts:post', kwargs={'username': self.user,
                                  'post_id': self.post.id}))
        author = response.context.get('post').author
        image = response.context.get('post').image
        self.assertEqual(author, self.user)
        self.assertEqual(response.context.get('post'), self.post)
        self.assertEqual(image, self.post.image)
