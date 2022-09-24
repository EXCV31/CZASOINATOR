import sys
import logging

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')

def exit_program(exit_code):
    """Store logs about exit and... just exit"""

    logging.info("Wyjście z aplikacji")
    sys.exit(exit_code)