# tex_doc_mngr
TDM - (La)TeX Document Manager

## Cel projektu
Celem projektu jest stworzenie systemu do obsługi czasopism naukowych

## Uruchomienie
1. Po sklonowaniu projektu należy utworzyć dwa pliki zawierające:
    - `.env`
        ```
        APP_MAIN_DIR=<ścieżka w której ma być zawarta mehanika aplikacji>
        DOC_FILES_DIR=<ścieżka w której będą przechowywane dane użytkowników>
        NGINX_OUTER_PORT=<port na który ma być udostępniana usługa>
        ```
    - `.psql.env`
        ```
        POSTGRES_DB=<nazwa bazy>
        POSTGRES_USER=<nazwa użytkownika bazy>
        POSTGRES_PASSWORD=<hasło użytkonika>
        ```
2. Uruchomić projekt będąc w głównym folderze przez odpalenie komendy:\
    `docker compose up --build -d`
3. Można wejść na stronę `http://127.0.0.1:<NGINX_OUTER_PORT>`\
    proponowany port to 80, więc adres to [127.0.0.1:80](http://127.0.0.1:80)
4. By zamknąć projekt należy uruchomić komendę:\
    `docker compose down`

