from datetime import datetime, timedelta
from typing import Optional


def parse_year_filter(time_filter: Optional[int]) :
   
    now = datetime.now()
    current_year = now.year
    year = time_filter or current_year

    start = datetime(year, 1, 1)
    if year == current_year:
        # Add one day to the current date and set time to midnight
        end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        end = datetime(year + 1, 1, 1)
    return start, end