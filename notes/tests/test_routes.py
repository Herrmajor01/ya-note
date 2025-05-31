"""Тесты доступности маршрутов приложения заметок."""

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты доступности страниц заметок."""

    @classmethod
    def setUpTestData(cls):
        """Настраивает тестовые данные для всех методов класса."""
        cls.author = User.objects.create(username='author')
        cls.reader = User.objects.create(username='reader')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            slug='test-zametka',
            author=cls.author
        )

    def test_home_page_available_for_anonymous(self):
        """Проверяет доступ к главной страницы для анонимного пользователя."""
        response = self.client.get(reverse('notes:home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authenticated_user_pages_access(self):
        """Проверяет доступность страниц для авторизованного пользователя."""
        self.client.force_login(self.author)
        urls = (
            ('notes:list', None, HTTPStatus.OK),
            ('notes:success', None, HTTPStatus.OK),
            ('notes:add', None, HTTPStatus.OK),
        )
        for name, args, expected_status in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_note_specific_pages_for_author_only(self):
        """Проверяет доступ к страницам заметок только для автора."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, expected_status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user.username, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, expected_status)
            self.client.logout()

    def test_anonymous_redirected_to_login(self):
        """Проверяет редирект анонимного пользователя на страницу логина."""
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                expected_url = f"{reverse('users:login')}?next={url}"
                self.assertRedirects(response, expected_url)

    def test_auth_pages_available_for_all(self):
        """Проверяет доступность страниц авторизации для всех пользователей."""
        urls = (
            ('users:login', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_available_for_all(self):
        """Проверяет доступность страницы выхода для всех пользователей."""
        # Проверяем для анонимного пользователя
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверяем для авторизованного пользователя
        self.client.force_login(self.author)
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
