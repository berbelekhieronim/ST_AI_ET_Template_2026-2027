# Interaktywny brief badania dla AI — Tobii X120

[Otwórz plik formularza w repozytorium](./brief-replikacja-tobii-x120.html).
GitHub pokazuje pod tym linkiem kod HTML, a nie działający formularz.

## Uruchomienie bez instalacji

1. Otwórz plik `brief-replikacja-tobii-x120.html` w repozytorium.
2. Pobierz go przyciskiem **Download raw file**. Zachowaj rozszerzenie `.html`.
3. Otwórz pobrany plik w aktualnej przeglądarce, np. Chrome, Edge, Firefox lub Safari.
4. Wypełnij kartę zespołu. Sprawdź komunikat o zapisie lokalnym.

Formularz jest samodzielny, działa offline i nie wymaga Pythona, SDK ani serwera.
Nie łączy się z eye-trackerem. Służy do przygotowania protokołu i briefu.
Obsługę Tobii X120 trzeba osobno potwierdzić dla wersji SDK i środowiska laboratorium.

## Wybór badania i podsumowanie

- W polu **Kolor zespołu** wybierz `red`, `blue`, `black`, `white`, `yellow` lub
  `pink`. Obok pojawi się próbka koloru; jego nazwa trafia do briefu i kopii JSON.
- W polu **Rodzaj badania** wybierz **Replikacja ze zmianą** lub **Badanie własne**.
- Przy badaniu własnym checkbox w sekcji **Oryginalne badanie** zaznacza się
  automatycznie. Pola z publikacji oraz kolumna oryginalnego badania znikają
  i nie trafiają do briefu ani wydruku. Nie trzeba ich wypełniać.
- Przełączenie rodzaju badania nie usuwa odpowiedzi. Są zachowane w JSON,
  aby można było wrócić do replikacji bez utraty pracy.
- Zieloną sekcję **Podsumowanie zespołu** studenci wypełniają własnymi słowami,
  nawet jeśli AI pomogło im uzupełnić pozostałe sekcje w VS Code.
- Podgląd briefu odświeża się automatycznie. Przyciski eksportu znajdują się
  na początku i na końcu formularza.

## Zapis, praca zespołowa i eksport

- Każda zmiana zapisuje się w `localStorage` tej przeglądarki. Błąd zapisu jest widoczny.
- Zapis nie jest synchronizowany z GitHubem, chmurą ani komputerami innych osób.
- Zmiana nazwy lub położenia pliku, przeglądarki, urządzenia albo adresu strony może
  odłączyć dotychczasowy zapis. Tryb prywatny i czyszczenie danych mogą go usunąć.
- **Kopia odpowiedzi (.json)** zapisuje aktualne pola i checkboxy. Pobieraj ją
  przed zamknięciem pracy, przeniesieniem pliku i przekazaniem go innej osobie.
- **Wczytaj kopię (.json)** odtwarza odpowiedzi po walidacji i potwierdzeniu.
  Zastępuje całą kartę; nie scala równoległych wersji zespołu.
- Starsze kopie JSON można nadal wczytać. Odpowiedzi z usuniętych pól trafiają
  do `archived_fields` w nowej kopii JSON, ale nie do briefu. Po wczytaniu
  sprawdź rodzaj badania — starsza karta nie zawierała tego wyboru.
  Dawna tekstowa nazwa zespołu jest zachowana jako `archived_fields.legacy_team_name`;
  po wczytaniu wybierz kolor zespołu.
- **Pobierz brief dla AI (.md)** tworzy czytelny tekst z odpowiedziami,
  zaznaczeniami, brakami oraz instrukcjami dotyczącymi weryfikacji SDK.
  Można otworzyć go jako tekst i wkleić do AI. Sam formularz niczego do AI nie wysyła.
- **Drukuj / zapisz PDF** korzysta z systemowego okna drukowania. Wybierz zapis
  jako PDF. Długie odpowiedzi są rozwijane do wydruku; sprawdź podgląd stron.
  PDF jest dokumentem do czytania, nie kopią do ponownego importu.
- Nie wpisuj danych osobowych uczestników, haseł, tokenów ani surowych danych pomiarowych.

## Publikacja przez GitHub Pages — dla administratora

Nie trzeba zmieniać kodu ani instalować zależności. Publikacja jest opcjonalna;
pobrany plik działa również bez niej.

1. Scal pull request z formularzem do `main`.
2. W repozytorium otwórz **Settings → Pages → Build and deployment**.
3. Wybierz **Source: Deploy from a branch**, gałąź **main** i katalog **/ (root)**.
4. Zapisz ustawienia i poczekaj na zakończenie wdrożenia `pages-build-deployment`.
5. Otwórz adres wdrożenia wskazany w ustawieniach Pages, dopisując
   `/brief-replikacja-tobii-x120.html`.

Dla forka `berbelekhieronim`, bez własnej domeny, oczekiwany adres po wdrożeniu to:

https://berbelekhieronim.github.io/ST_AI_ET_Template_2026-2027/brief-replikacja-tobii-x120.html

Dla repozytorium źródłowego:

https://eyelab-swps-wr.github.io/ST_AI_ET_Template_2026-2027/brief-replikacja-tobii-x120.html

To adres docelowy, nie potwierdzenie aktywnej publikacji. Nie jest wymagany
`index.html`, jeżeli użytkownicy otwierają pełny adres pliku. Dla forka użyj
adresu wdrożenia jego właściciela. Jeżeli Pages jest wyłączone przez zasady
organizacji lub konta, administrator musi najpierw rozwiązać to ograniczenie.
Włączenie Pages nie daje studentom prawa zapisu w repozytorium.

## Sprawdzenie po wdrożeniu

1. Otwórz pełny adres HTTPS formularza: powinien pokazać kartę, nie kod HTML ani 404.
2. Wpisz tekst z polskimi znakami i nową linią, wybierz opcję oraz zaznacz checkbox.
3. Odśwież stronę i sprawdź, czy odpowiedzi wróciły.
4. Pobierz JSON i Markdown. Sprawdź, czy oba zawierają bieżące odpowiedzi,
   a Markdown poprawnie rozróżnia wymagania od wykonanych testów.
5. Pobierz kopię, wyczyść kartę, wczytaj JSON i porównaj pola oraz zaznaczenia.
6. Sprawdź podgląd wydruku z długą odpowiedzią i zapisz próbny PDF.
7. Usuń testowe odpowiedzi. Nie przeprowadzaj tych testów na jedynej kopii pracy zespołu.

Zapis pod adresem Pages jest oddzielny od zapisu pobranego pliku HTML.
Do przeniesienia pracy między tymi wersjami użyj kopii JSON.
