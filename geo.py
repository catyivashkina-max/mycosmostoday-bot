from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


geolocator = Nominatim(user_agent="mycosmostoday_bot")
timezone_finder = TimezoneFinder()


def get_city_data(city_name: str):
    location = geolocator.geocode(
        city_name,
        language="ru",
        timeout=10
    )

    if not location:
        location = geolocator.geocode(
            f"{city_name}, Россия",
            language="ru",
            timeout=10
        )

    if not location:
        return None

    latitude = location.latitude
    longitude = location.longitude

    timezone = timezone_finder.timezone_at(
        lat=latitude,
        lng=longitude
    )

    return {
        "name": location.address,
        "lat": latitude,
        "lng": longitude,
        "timezone": timezone
    }