# CZASOINATOR

Śledź swoje postępy przy zadaniach w Redmine z CZASOINATOREM!

# Zrzuty ekranu:
<img align="left" title="W sumie całkiem fajne to wyszło" src="https://raw.githubusercontent.com/EXCV31/CZASOINATOR/main/screenshot.png" />
⠀
⠀
<img align="left" title="W sumie całkiem fajne to wyszło" src="https://raw.githubusercontent.com/EXCV31/CZASOINATOR/main/screenshot2.png" />

# Opis:
Projekt zaczęty jako niepoważny, który z czasem stał się pół-poważny. Początkowo w założeniu miał to być tylko prosty stoper, 
potem miała być to aplikacja okienkowa, jednak nie znalazłem chęci do tworzenia GUI - więc skończyła jako pseudogui w konsoli.

CZASOINATOR - Jest to prosty program do śledzenia swojej aktywności w Redmine. Programu nie mam zamiaru tłumaczyć na język angielski, 
dlatego dokumentacja i opis funkcjonalności powstała tylko po polsku, z przymrużeniem oka. Narzędzie testowane i używane na systemie Linux, jednak na Windows oraz MacOS powinno działać bez problemu.

## Funkcje:

### 1. Uruchom zliczanie czasu - Uruchom stoper, popracuj trochę, zatrzymaj. Po wszystkim CZASOINATOR wrzuci Twoje postępy do Redmine!

* Pobranie od użytkownika ID zadania w Redmine
* Pytanie: Czy wybrano poprawne zadanie + pokazanie tytułu zadania
* Uruchomienie licznika
* Oczekiwanie na sygnał od użytkownika o chęci zakończenia zliczania
* Zatrzymanie licznika
* Pokazanie ilości przepracowanych godzin
* Pobranie od użytkownika komentarza opisującego postępy
* Pytanie: Czy chcesz wrzucić przepracowany czas do Redmine?
  * Dodanie przepracowanego czasu do wskazanego zadania
* Umieszczenie w bazie: Data, numer zadania, tytuł zadania, przepracowany czas, komentarz

### 2. Sprawdź dzisiejsze postępy - Przydatne na daily

* Wykonanie zapytania o wszystkie rekordy z dzisiaj
* Wyświetlenie rekordów z rozróżnieniem przed/po daily lub komunikatu o braku rekordów w bazie

### 3. Sprawdź wczorajsze postępy - Przydatne na daily
* Rozpoznanie dnia - uruchomiony w poniedziałek pokaże rekordy z piątku
* W przeciwnym razie pokaże wczorajsze
* Wyświetlenie rekordów z rozróżnieniem przed/po daily lub komunikatu o braku rekordów w bazie

### 4. Dorzuć ręcznie czas do zadania 

* Pobranie od użytkownika ID zadania w Redmine
* Pytanie: Czy wybrano poprawne zadanie + pokazanie tytułu zadania
* Pobranie od użytkownika ilości przepracowanych godzin
* Pobranie od użytkownika komentarza opisującego postępy
* Dodanie przepracowanego czasu do wskazanego zadania
* Umieszczenie w bazie: Data, numer zadania, tytuł zadania, przepracowany czas, komentarz

### 5. Dorzuć ręcznie czas do bazy - własne zadanie - Przydatne na demo, konsultacje i inne

* Pobranie od użytkownika nazwy zadania
* Pobranie od użytkownika ilości przepracowanych godzin
* Umieszczenie w bazie: Data, tytuł zadania, przepracowany czas

### 6. Statystyki

* Wykonanie zapytanie o wszystkie rekordy z kolumny SPEDZONY_CZAS
* Obrobienie pobranych danych
* Wyświetlenie ilości przepracowanych ogółem godzin w bazie

## Do zrobienia:
* Dodanie funkcjonalności komentowania do kroku nr 5 - dodanie własnego zadania do bazy.
* Refaktoryzacja wg Pep8

## Użycie:

### Do instalacji:
* pip install -r requirements.txt

### Do wypełnienia:
# Config.ini:
* ADDRESS= Adres redmine
* API_KEY= Klucz API
* DAILY= Godzina daily w formacie HH:MM:SS
* EXCLUDE= Opcjonalnie - Które projekty ominąć przy listowaniu zadań należących do użytkownika, oddzielone przecinkiem
* INSTANCE= Opcjonalnie - Na której instacji aktualnie pracujemy, może służyć także jako nazwa firmy wyświetlana po uruchomieniu programu na belce

# Przykładowe wypełnienie:
[REDMINE]
ADDRESS=http://demo.redmine.org
API_KEY=21pye5a470d08f83130b5e001bdkh56ff68f0416
DAILY=11:00:00
EXCLUDE=Samochody
INSTANCE=DEV/Stage
