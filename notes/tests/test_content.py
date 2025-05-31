"""Тесты содержимого и контекста страниц."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    """Тесты содержимого страниц заметок."""

    @classmethod
    def setUpTestData(cls):
        """Настраивает данные для всех тестов класса."""
        cls.author = User.objects.create(username='author')
        cls.other_user = User.objects.create(username='other_user')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            slug='test-zametka',
            author=cls.author
        )

    def test_note_in_object_list_for_author(self):
        """Проверяет, что заметка автора видна в списке."""
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertEqual(list(object_list), [self.note])

    def test_no_notes_for_other_user(self):
        """Проверяет, что чужие заметки не видны."""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertEqual(list(object_list), [])

    def test_form_on_add_and_edit_pages(self):
        """Проверяет наличие формы на страницах создания и редактирования."""
        self.client.force_login(self.author)
        urls = (
            reverse('notes:add'),
            reverse('notes:edit', args=(self.note.slug,)),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
