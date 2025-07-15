import requests
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm # For login, registration and logout
from django.contrib.auth.decorators import login_required
from datetime import datetime, timezone
import pytz

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
    return emoji_map.get(icon_name, 'unknown weather')

def index(request):
    city = request.GET.get('city')
    geocoding_api = '68756eb49e4a686df0b5652c27e6f3e9' # from openweathermap, because pirate weather's api is not specialized in geocoding
    api_key = 'JAev9U7MjerdnQ1yyDRjTgbPodzYW8dY' # from pirate weather

    context = {}
    
    if city:
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={geocoding_api}"
        geocode_response = requests.get(geocode_url).json()

        lat = geocode_response[0]['lat']
        lon = geocode_response[0]['lon']
        city_display_name = geocode_response[0].get('name', city)
        country_display = geocode_response[0].get('country', '')

        weather_url = (f"https://api.pirateweather.net/forecast/{api_key}/{lat},{lon}?"
                              f"units=si&exclude=minutely,alerts,flags"
                              f"&extend=hourly")

        weather_response = requests.get(weather_url).json()

        timezone_name = weather_response.get('timezone')
        
        city_timezone = pytz.timezone(timezone_name)
        
        current_data = weather_response['currently']
        context['city'] = city_display_name
        context['country'] = country_display
        context['temperature'] = current_data['temperature']
        context['description'] = current_data.get('summary', 'N/A').capitalize()
        context['icon'] = getWeather(current_data.get('icon'))

        if request.user.is_authenticated:
            weekly_forecast = []
            daily_data_list = weather_response.get('daily', {}).get('data', [])

            for day_entry in daily_data_list:
                dt_utc_aware = datetime.fromtimestamp(day_entry['time'], tz=timezone.utc)
                dt_local_aware = dt_utc_aware.astimezone(city_timezone)

                weekly_forecast.append({
                    'date': dt_local_aware.strftime('%A, %b %d'),
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
    if request.method == 'POST': # means the form has been submited
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
        
    return render(request, 'weather/register.html', {'form': form})
        
def custom_login(request): 
    if request.method == 'POST': # means the form has been submited
        form = AuthenticationForm(request, data = request.POST)
        if form.is_valid():
            f_username = form.cleaned_data.get('username')
            f_password = form.cleaned_data.get('password')
            user = authenticate(request, username = f_username, password = f_password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
        
    return render(request, 'weather/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')
    
            