from datetime import date
from config.setup_config_and_connection import parse_config
from helpers.error_handler import display_error
from helpers.exit_handler import exit_program
from helpers.colors import get_color
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text




logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')
console = Console()

def show_days_off():
    _, config, _ = parse_config()
    off_days_per_year = config["OFF_DAYS_PER_YEAR"]
    current_date = date.today()

    with open("cache/days_off.cache", "r") as cache:

        # Assertion zone. Check if user correctly filled values in config and cache.
        try:
            days_off, year = cache.readlines()[0].split(",")
            year = int(year)
            days_off = int(days_off)
            off_days_per_year = int(off_days_per_year)
        except ValueError:
            display_error("Błąd parsowania cache dni urlopowych lub klucza OFF_DAYS_PER_YEAR w config/config.ini. Sprawdź poprawne wypełnienie tych plików.")
            exit_program(1)
        
        # Check if year has changed. If yes, add some days off to cache, you deserve it :)
        if year < current_date.year:
            logging.info(f"Minął kolejny rok, dodano {off_days_per_year} dni urlopowych do cache.")
            console.rule(f"[{get_color('bold_blue')}]Szczęśliwego nowego roku! Dodano {off_days_per_year} dni urlopowych :)")
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
            old_days_off = "brak"
        else:
            days_off = days_off - old_days_off

        console.print(Panel(Text(f"\nPozostałe dni urlopowe (nowe): {days_off}\n"
                                f"\nPozostałe dni urlopowe (stare): {old_days_off}\n"
                                , justify="center", style="white")
                        , style=get_color("light_blue"), title=f"[{get_color('bold_orange')}]CZASOINATOR"))

        

def change(amount, year):
    with open("cache/days_off.cache", "w") as cache:
        cache.write(f"{amount}, {year}")

