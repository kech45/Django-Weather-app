import requests
from datetime import datetime, timezone
import pytz
import os

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import SearchHistory


def getWeather(icon_name):
    emoji_map = {
        'clear': '☀️',
        'clear-day': '☀️',
        'clear-night': '🌙',
        'rain': '🌧️',
        'snow': '❄️',
        'sleet': '🌨️',
        'wind': '💨',
        'fog': '🌫️',
        'cloudy': '☁️',
        'partly-cloudy-day': '🌤️',
        'partly-cloudy-night': '☁️',
        'hail': '🧊',
        'thunderstorm': '⛈️',
        'tornado': '🌪️',
        'unknown': '❓'
    }
    return emoji_map.get(icon_name, '❓')


def index(request):
    city = request.GET.get('city')

    geocoding_api = settings.OPENWEATHER_API_KEY
    api_key = settings.PIRATEWEATHER_API_KEY

    context = {}

    if city:
        geocode_url = (
            f"http://api.openweathermap.org/geo/1.0/direct"
            f"?q={city}&limit=1&appid={geocoding_api}"
        )
        geocode_response = requests.get(geocode_url).json()

        if not geocode_response:
            context['error'] = "City not found."
            return render(request, 'weather/index.html', context)

        lat = geocode_response[0]['lat']
        lon = geocode_response[0]['lon']
        city_display_name = geocode_response[0].get('name', city)
        country_display = geocode_response[0].get('country', '')

        weather_url = (
            f"https://api.pirateweather.net/forecast/{api_key}/{lat},{lon}"
            f"?units=si&exclude=minutely,alerts,flags&extend=hourly"
        )

        weather_response = requests.get(weather_url).json()

        timezone_name = weather_response.get('timezone')
        city_timezone = pytz.timezone(timezone_name)

        current_data = weather_response['currently']

        temperature = current_data['temperature']
        description = current_data.get('summary', 'N/A').capitalize()
        icon = getWeather(current_data.get('icon'))

        context.update({
            'city': city_display_name,
            'country': country_display,
            'temperature': temperature,
            'description': description,
            'icon': icon,
        })

        # ✅ SAVE SEARCH HISTORY
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                city=city_display_name,
                country=country_display,
                temperature=temperature,
                description=description,
                icon=icon,
            )

            weekly_forecast = []
            daily_data_list = weather_response.get('daily', {}).get('data', [])

            for day_entry in daily_data_list:
                dt_utc = datetime.fromtimestamp(day_entry['time'], tz=timezone.utc)
                dt_local = dt_utc.astimezone(city_timezone)

                weekly_forecast.append({
                    'date': dt_local.strftime('%A, %b %d'),
                    'min_temp': day_entry['temperatureMin'],
                    'max_temp': day_entry['temperatureMax'],
                    'description': day_entry.get('summary', 'N/A').capitalize(),
                    'icon': getWeather(day_entry.get('icon')),
                })

            context['weekly_forecast'] = weekly_forecast
        else:
            context['guest'] = True

    else:
        context['message'] = "Enter a city to get the weather forecast."

    return render(request, 'weather/index.html', context)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'weather/register.html', {'form': form})


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()

    return render(request, 'weather/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required
def search_history(request):
    searches = SearchHistory.objects.filter(user=request.user)[:20]
    return render(request, 'weather/history.html', {
        'searches': searches
    })


@login_required
def delete_history(request, history_id):
    SearchHistory.objects.filter(
        id=history_id,
        user=request.user
    ).delete()
    return redirect('search_history')


@login_required
def clear_all_history(request):
    SearchHistory.objects.filter(user=request.user).delete()
    return redirect('search_history')
