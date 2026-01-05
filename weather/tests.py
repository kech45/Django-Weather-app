from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from weather.views import getWeather
from weather.models import SearchHistory

class WeatherEmojiTest(TestCase):
    """Unit tests for weather emoji mapping"""

    def test_weather_emoji_mapping(self):
        self.assertEqual(getWeather('clear-day'), '☀️')
        self.assertEqual(getWeather('rain'), '🌧️')
        self.assertEqual(getWeather('snow'), '❄️')
        self.assertEqual(getWeather('cloudy'), '☁️')
        self.assertEqual(getWeather('invalid'), '❓')


class SearchHistoryModelTest(TestCase):
    """Tests for SearchHistory model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_search_history_creation(self):
        history = SearchHistory.objects.create(
            user=self.user,
            city='Sofia',
            country='BG',
            temperature=15.5,
            description='Sunny',
            icon='☀️'
        )

        self.assertEqual(SearchHistory.objects.count(), 1)
        self.assertEqual(history.city, 'Sofia')

class IndexViewTest(TestCase):
    """Integration tests for index view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.url = reverse('index')

    def test_index_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @patch('weather.views.requests.get')
    def test_authenticated_search_saves_history(self, mock_get):
        """Authenticated users should have searches saved"""

        self.client.login(username='testuser', password='testpass123')

        mock_geocode = MagicMock()
        mock_geocode.json.return_value = [{
            'lat': 42.6977,
            'lon': 23.3219,
            'name': 'Sofia',
            'country': 'BG'
        }]

        mock_weather = MagicMock()
        mock_weather.json.return_value = {
            'timezone': 'Europe/Sofia',
            'currently': {
                'temperature': 15.5,
                'summary': 'clear',
                'icon': 'clear-day'
            },
            'daily': {'data': []}
        }

        mock_get.side_effect = [mock_geocode, mock_weather]

        self.client.get(self.url, {'city': 'Sofia'})

        self.assertEqual(SearchHistory.objects.count(), 1)
        self.assertEqual(SearchHistory.objects.first().city, 'Sofia')

    @patch('weather.views.requests.get')
    def test_guest_search_does_not_save_history(self, mock_get):
        """Guest users should NOT have search history saved"""

        mock_geocode = MagicMock()
        mock_geocode.json.return_value = [{
            'lat': 42.6977,
            'lon': 23.3219,
            'name': 'Sofia',
            'country': 'BG'
        }]

        mock_weather = MagicMock()
        mock_weather.json.return_value = {
            'timezone': 'Europe/Sofia',
            'currently': {
                'temperature': 15.5,
                'summary': 'clear',
                'icon': 'clear-day'
            },
            'daily': {'data': []}
        }

        mock_get.side_effect = [mock_geocode, mock_weather]

        self.client.get(self.url, {'city': 'Sofia'})

        self.assertEqual(SearchHistory.objects.count(), 0)

class AuthenticationTest(TestCase):
    """Basic authentication flow tests"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_user_login(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'testpass123'}
        )
        self.assertEqual(response.status_code, 302)

    def test_user_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class SearchHistoryViewTest(TestCase):
    """Tests for search history access control"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_history_requires_login(self):
        response = self.client.get(reverse('search_history'))
        self.assertEqual(response.status_code, 302)
