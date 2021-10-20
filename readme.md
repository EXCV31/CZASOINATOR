# CZASOINATOR

Śledź swoje postępy przy zadaniach w Redmine z CZASOINATOREM!

# Zrzuty ekranu:
<img align="left" title="W sumie całkiem fajne to wyszło" src="https://raw.githubusercontent.com/EXCV31/CZASOINATOR/main/screenshot.png" />
⠀
⠀
<img align="left" title="W sumie całkiem fajne to wyszło" src="https://raw.githubusercontent.com/EXCV31/CZASOINATOR/main/screenshot2.png" />

## Opis
Projekt zaczęty jako niepoważny, który z czasem stał się pół-poważny. Początkowo w założeniu miał to być tylko prosty stoper, 
potem miała być to aplikacja okienkowa, jednak nie znalazłem chęci do tworzenia GUI - więc skończyła jako pseudogui w konsoli.

CZASOINATOR - Jest to prosty program do śledzenia swojej aktywności w Redmine. Programu nie mam zamiaru tłumaczyć na język angielski, 
dlatego dokumentacja i opis funkcjonalności powstała tylko po polsku, z przymrużeniem oka. Narzędzie testowane i używane na systemie Linux, jednak na Windows oraz MacOS powinno działać bez problemu.

## Funkcje

### 1. Uruchom zliczanie czasu - Uruchom stoper, popracuj trochę, zatrzymaj. Po wszystkim CZASOINATOR wrzuci Twoje postępy do Redmine!

* Uruchomienie stopera po wpisaniu ID zadania. Po zakończeniu pracy wrzucenie czasu do redmine oraz do lokalnej bazy danych. Jako feature przypominajka o commit/push wraz z przetłumaczonym komentarzem na angielski.

### 2. Sprawdź dzisiejsze postępy - Przydatne na daily

* Odpytanie bazy danych o rekordy z dnia dzisiejszego. Wyświetlane w formie tabeli.

### 3. Sprawdź wczorajsze postępy - Przydatne na daily

* Odpytanie bazy danych o rekordy z dnia wczorajszego, w przypadku uruchomienia tego w poniedziałek odpytuje 3 dni wstecz (piątek). Wyświetlane w formie tabeli.

### 4. Dorzuć ręcznie czas do zadania 

* Po wpisaniu ID zadania i przepracowanego czasu wrzucenie tego do redmine i lokalnej bazy.

### 5. Dorzuć ręcznie czas do bazy - własne zadanie - Przydatne na demo, konsultacje i inne

* Odpytanie o nazwę zadania, przepracowane godziny oraz komentarz, i wrzucenie tego do lokalnej bazy.

### 6. Sprawdź zadania przypisane do Ciebie - gdy nie wiesz czym się zająć

* Odpytanie redmine o zagadnienia przypisane do ID użytkownika - pobierane przez API key. Wyświetlane w formie tabeli. W przypadku braku zadań wyświetlany odpowiedni komunikat. W przypadku "lepszych" terminali po kliknięciu LPM wraz z CTRL w numer zadania zostanie otworzona przeglądarka z tym zadaniem.

### 7. Statystyki

* Odpytanie o wszystkie rekordy z bazy danych, zsumowanie czasu i przedstawienie użytkownikowi.


## Użycie

### Do instalacji:
* pip install -r requirements.txt

### Do wypełnienia:

#### Config.ini:
* ADDRESS= Adres redmine
* API_KEY= Klucz API
* DAILY= Godzina daily w formacie HH:MM:SS
* EXCLUDE= Opcjonalnie - Które projekty ominąć przy listowaniu zadań należących do użytkownika, oddzielone przecinkiem
* PROGRAMMER_MODE= Opcjonalnie - w przypadku ustawienia wartości "true" przy zakończeniu prac zostanie pokazana przypominajka o git commit z numerem taska oraz przetłumaczonym na język angielski komentarzem.

#### Przykładowe wypełnienie:
* [REDMINE]
* ADDRESS=http://demo.redmine.org
* API_KEY=21pye5a470d08f83130b5e001bdkh56ff68f0416
* DAILY=11:00:00
* EXCLUDE=Samochody
* PROGRAMMER_MODE=true


