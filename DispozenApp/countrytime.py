from datetime import datetime
import pytz

def get_timezone_from_iso_code(iso_code):
    country_timezones = {
        "CA": "America/Toronto",  # Canada (Eastern Time)
        "FR": "Europe/Paris",     # France (Central European Time)
        "IT": "Europe/Rome",      # Italy (Central European Time)
        "ES": "Europe/Madrid",    # Spain (Central European Time)
        "PT": "Europe/Lisbon",    # Portugal (Western European Time)
        "GB": "Europe/London",    # England (Greenwich Mean Time)
        "BD": "Asia/Dhaka",       # Bangladesh (Bangladesh Standard Time)
        # Add more country codes and timezones here if needed
    }

    return country_timezones.get(iso_code)

def convert_utc_to_local(day_time, iso_code):

        utc_time = day_time


        utc_time_str = utc_time.strftime("%H:%M:%S")


        utc_time_with_date = datetime.combine(datetime.today(), utc_time, tzinfo=pytz.utc)

        
        bd_zone = pytz.timezone('Asia/Dhaka')
        bd_time = utc_time_with_date.astimezone(bd_zone)


        
        return bd_time