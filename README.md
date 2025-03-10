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
        ```
    - `.nginx.env` 
        ```
        NGINX_OUTER_PORT=<port na który ma być udostępniana usługa http>
        NGINX_HTTPS_OUTER_PORT=<port na który ma być udostępniana usługa https>
        CERT_DIR=<ścieżka w której będą przechowywane certyfikaty ssl do https>
        ```
    - `.python.env` 
        ```
        FLASK_KEY=<sekretny klucz aplikacji flask>
        MAIL_HOST=<adres serwera smtp>
        MAIL_PORT=<port serwera smtp>
        MAIL_ADDRESS=<adres email wysyłającego>
        MAIL_USERNAME=<nick wysyłającego na serwerze email>
        MAIL_PASSWORD=<hasło wysyłającego na serwerze email>
        MAIL_AUTH_TYPE=<typ autoryzacji: ssl|tls|plain|none>
        DOC_FILES_DIR=<ścieżka w której będą przechowywane dane użytkowników>
        TEMP_FOLDER=<ścieżka gdzie będą przechowywane tymczasowo pliki latex do pogdlądu jako pdf>
        PEPPER_VAL=<wartość pieprzu dodawanego do haseł>
        ```
        komenda do wygenerowania sekretnego klucza: `python -c 'import os; print(os.urandom(24).hex())'`
        przykładowa komenda do wygenerowania pieprzu: `python -c 'import os; print(os.urandom(12).hex())'`
    - `.psql.env`
        ```
        POSTGRES_DB=<nazwa bazy>
        POSTGRES_USER=<nazwa użytkownika bazy>
        POSTGRES_PASSWORD=<hasło użytkownika>
        ```
3. By uruchomić projekt będąc w głównym folderze należy uruchomić komendę:\
    `docker compose up --build -d`
4. Można wejść na stronę `http://127.0.0.1:<NGINX_OUTER_PORT>`\
    proponowany port to 80, więc adres to [127.0.0.1:80](http://127.0.0.1:80)
5. By zamknąć projekt należy uruchomić komendę:\
    `docker compose down`
