# App 6 - Kaskada Spojrzenia i Wybor

Krotka demonstracja inspirowana badaniem Shimojo i in. (2003), "Gaze bias both
reflects and influences preference".

## Uruchomienie

- Windows: uruchom `run_app6.bat`.
- Linux/macOS: uruchom `bash run_app6.sh`.

Wymagany jest Python 3 i PsychoPy. Skrypt uzywa do pomiaru czasu odswiezania
ekranu, a przy braku pomiaru przyjmuje 60 Hz.

## Przebieg

Uczestnik porownuje pare abstrakcyjnych figur przed i po ich szesciokrotnej,
naprzemiennej prezentacji. Cztery z osmiu prob wykorzystuja nierowna ekspozycje
(900/300 ms), a cztery kontrole rowna ekspozycje (600/600 ms). Kolejnosc prob,
strona dluzszej ekspozycji i kolejnosc pierwszej prezentacji sa losowane.

Odpowiedzi sa zapisywane w lokalnym pliku `app6_session_<kod>_<czas>.csv`.
Kod uczestnika nie powinien zawierac imienia ani nazwiska.

## Interpretacja

To demonstracja dydaktyczna, nie pelna replikacja badania. Nie ma eye-trackera,
proby sa nieliczne, a materialy to losowe figury. Nie da sie oddzielic samego
kierunku spojrzenia od dluzszej ekspozycji ani wyciagac wnioskow o pojedynczym
uczestniku.
