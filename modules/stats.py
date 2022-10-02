from config.setup_config_and_connection import frame_title
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# File imports
from database.setup_db import cursor
from helpers.colors import get_color
from helpers.convert_float import float_to_hhmm

console = Console()


def show_stats():
    """
    Show stats about usage to user - data is taken from database, not from redmine.

    Returns:

    """

    cursor.execute("SELECT SPEDZONY_CZAS FROM BAZA_DANYCH")
    rows = cursor.fetchall()
    total_hours = 0

    for row in rows:
        total_hours += float(row[0])

    # Convert float time to HH:MM
    total_hours = float_to_hhmm(total_hours)

    console.print("", Panel(Text(
        f"\n Czas spędzony z CZASOINATOREM: {total_hours.split(':')[0]} godzin, {total_hours.split(':')[1]} minut\n",
        justify="center", style="white"),
        style=get_color("light_blue"), title=frame_title))
