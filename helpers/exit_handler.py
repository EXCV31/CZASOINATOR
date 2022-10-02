import sys
import logging
from database.setup_db import conn
logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')


def exit_program(exit_code):
    """
    Close connection to database, store logs about exit and... just exit
    Args:
        exit_code: Exit code of script, I only use 1 or 0.

    Returns:

    """
    logging.info("Zamykanie bazy danych...")
    
    conn.close()

    logging.info("Wyjście z aplikacji")
    sys.exit(exit_code)
