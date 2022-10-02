from datetime import date
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# File imports
from config.setup_config_and_connection import redmine_conf, frame_title
from helpers.error_handler import display_error
from helpers.colors import get_color

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')
console = Console()


def show_days_off():
    """
    The function is used to calculate and show the user how many vacation days he or she has left,
    and is a sort of diary that tracks instead of us the question of how many vacation days we have left.

    Returns:

    """

    off_days_per_year = redmine_conf["OFF_DAYS_PER_YEAR"]
    current_date = date.today()

    with open("cache/days_off.cache", "r") as cache:

        # Assertion zone. Check if user correctly filled values in config and cache.
        try:
            days_off, year = cache.readlines()[0].split(",")
            year = int(year)
            days_off = int(days_off)
            off_days_per_year = int(off_days_per_year)
        except ValueError:
            display_error(
                "Błąd parsowania cache dni urlopowych lub klucza OFF_DAYS_PER_YEAR w config/config.ini."
                " Sprawdź poprawne wypełnienie tych plików.")
            return

        # Check if year has changed. If yes, add some days off to cache, you deserve it :)
        if year < current_date.year:
            logging.info(f"Minął kolejny rok, dodano {off_days_per_year} dni urlopowych do cache.")
            console.rule(
                f"[{get_color('bold_blue')}]Szczęśliwego nowego roku! Dodano {off_days_per_year} dni urlopowych :)")
            change(days_off + off_days_per_year, current_date.year)

    # Re-open file to get fresh data - file can be changed when there's new year.
    with open("cache/days_off.cache", "r") as cache:
        days_off = int(cache.readlines()[0].split(",")[0])

        # Calculate days off from last year. 
        # If days off in cache is greater than in config, it's means that we have some days off from last year.
        old_days_off = days_off - off_days_per_year

        # If we don't have off days from last year, simply display "none".
        # But if we have old vacation days, subtract them from the total vacation days.
        if old_days_off < 0:
            old_days_off = 0
        else:
            days_off = days_off - old_days_off
        print("")
        console.print(Panel(Text(f"\nPozostałe dni urlopowe (nowe): {days_off}\n"
                                 f"\nPozostałe dni urlopowe (stare): {old_days_off}\n", justify="center",
                                 style="white"), style=get_color("light_blue"), title=frame_title))

    choice = input("Idziesz na urlop? t/N: ")
    if choice.lower() == "t":
        print("")
        amount = input("Wpisz ilość dni: ")

        try:
            amount = int(amount)
        except ValueError:
            display_error("Błędna wartość dla pola: Ilość dni")
            return

        # Check if user typed a vacation days lower than zero or higher than his current vacation days.
        if amount <= 0 or amount > days_off + old_days_off:
            display_error("Błędna wartość dla pola: Ilość dni")
            return

        # Save new value to cache. 
        with open("cache/days_off.cache", "w") as cache:
            cache.write(f"{days_off + old_days_off - amount},{current_date.year}")

        console.print("", Panel(Text(f"\nDodano, miłego wypoczynku!"
                                     f"\n\nPozostało Ci w sumie {days_off + old_days_off - amount} dni urlopowych.\n",
                                     justify="center", style="white"), style=get_color("green"),
                                title=frame_title))


def change(amount, year):
    """
    Change data in cache/days_off.cache

    Args:
        amount: How many days to write to cache.
        year: Current year.

    Returns: New cache with amount of vacation days left, and year.
    """
    with open("cache/days_off.cache", "w") as cache:
        cache.write(f"{amount}, {year}")
