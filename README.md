# tex_doc_mngr
TDM - (La)TeX Document Manager

## Cel projektu
Celem projektu jest stworzenie systemu do obsługi czasopism naukowych

## Uruchomienie
1. Klonowanie projektu przez komendę:\
    `git clone git@github.com:zlog7918/tex_doc_mngr.git`\
    lub\
    `git clone https://github.com/zlog7918/tex_doc_mngr.git`
2. Po sklonowaniu projektu należy utworzyć dwa pliki w głównym folderze zawierające:
    - `.env`
        ```
        APP_MAIN_DIR=<ścieżka w której ma być zawarta mechanika aplikacji>
        DOC_FILES_DIR=<ścieżka w której będą przechowywane dane użytkowników>
        NGINX_OUTER_PORT=<port na który ma być udostępniana usługa>
        ```
    - `.psql.env`
        ```
        POSTGRES_DB=<nazwa bazy>
        POSTGRES_USER=<nazwa użytkownika bazy>
        POSTGRES_PASSWORD=<hasło użytkonika>
        ```
3. By uruchomić projekt będąc w głównym folderze należy uruchomić komendę:\
    `docker compose up --build -d`
4. Można wejść na stronę `http://127.0.0.1:<NGINX_OUTER_PORT>`\
    proponowany port to 80, więc adres to [127.0.0.1:80](http://127.0.0.1:80)
5. By zamknąć projekt należy uruchomić komendę:\
    `docker compose down`
