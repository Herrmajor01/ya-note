"""Тесты логики работы с заметками."""

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify
from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteLogic(TestCase):
    """Тесты логики создания, редактирования и удаления заметок."""

    @classmethod
    def setUpTestData(cls):
        """Настраивает данные для всех тестов класса."""
        cls.author = User.objects.create(username='author')
        cls.reader = User.objects.create(username='reader')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            slug='test-zametka',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Новый текст',
            'slug': 'novaya-zametka'
        }

    def test_authenticated_user_can_create_note(self):
        """Проверяет создание заметки авторизованным пользователем."""
        self.client.force_login(self.author)
        response = self.client.post(reverse('notes:add'), data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(slug=self.form_data['slug'])
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Проверяет, что аноним не может создать заметку."""
        response = self.client.post(reverse('notes:add'), data=self.form_data)
        login_url = f"{reverse('users:login')}?next={reverse('notes:add')}"
        self.assertRedirects(response, login_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_cant_create_note_with_duplicate_slug(self):
        """Проверяет невозможность создания заметки с дублирующимся slug."""
        self.client.force_login(self.author)
        self.form_data['slug'] = self.note.slug
        response = self.client.post(reverse('notes:add'), data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].errors['slug'], [
                         f'{self.note.slug}{WARNING}'])
        self.assertEqual(Note.objects.count(), 1)

    def test_auto_slug_generation(self):
        """Проверяет автоматическую генерацию slug."""
        self.client.force_login(self.author)
        form_data_no_slug = self.form_data.copy()
        del form_data_no_slug['slug']
        response = self.client.post(
            reverse('notes:add'), data=form_data_no_slug)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(title=form_data_no_slug['title'])
        expected_slug = slugify(form_data_no_slug['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Проверяет, что автор может редактировать свою заметку."""
        self.client.force_login(self.author)
        new_data = {
            'title': 'Обновлённая заметка',
            'text': 'Обновлённый текст',
            'slug': 'obnovlennaya-zametka'
        }
        response = self.client.post(
            reverse('notes:edit', args=(self.note.slug,)), data=new_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, new_data['title'])
        self.assertEqual(self.note.text, new_data['text'])
        self.assertEqual(self.note.slug, new_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Проверяет, другой пользователь не может редактировать заметку."""
        self.client.force_login(self.reader)
        new_data = {
            'title': 'Чужая заметка',
            'text': 'Чужой текст',
            'slug': 'chuzhaya-zametka'
        }
        response = self.client.post(
            reverse('notes:edit', args=(self.note.slug,)), data=new_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, new_data['title'])

    def test_author_can_delete_note(self):
        """Проверяет, что автор может удалить свою заметку."""
        self.client.force_login(self.author)
        response = self.client.delete(
            reverse('notes:delete', args=(self.note.slug,)))
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Проверяет, что другой пользователь не может удалить заметку."""
        self.client.force_login(self.reader)
        response = self.client.delete(
            reverse('notes:delete', args=(self.note.slug,)))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
