import os
import re
import tarfile
import zipfile
import subprocess
from flask import send_from_directory
from werkzeug.utils import secure_filename
from models.utils.Response import Response
from werkzeug.datastructures import FileStorage
from models.utils.MessageException import MessageException

class LatexService:
    @staticmethod
    def convert_tex_to_pdf(tex_path: str, output_dir: str) -> bool:
        try:
            pdf_path = os.path.join(output_dir, os.path.basename(tex_path).replace('.tex', '.pdf'))
            result=None
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "--shell-escape", "-interaction=nonstopmode", "-output-directory", output_dir,
                     tex_path],
                    cwd=os.path.dirname(tex_path),
                    check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            if result is not None and result.returncode != 0:
                print(result)
                print(result.returncode)
                print(f'cd \'{os.path.dirname(tex_path)}\'; \'{'\' \''.join(result.args)}\'')
                try:
                    raise Exception(f'{ {'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()} }')
                except Exception as e:
                    raise MessageException("LaTeX compilation failed", err=e) from None

            return os.path.exists(pdf_path)

        except subprocess.CalledProcessError as e:
            raise MessageException(str(e), err=e)

    @staticmethod
    def get_file(folder: str, filename: str) -> Response:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            return Response.success_response(send_from_directory(folder, filename))
        raise MessageException('Plik nie istnieje')

    @staticmethod
    def save_file(file: FileStorage, folder: str) -> str:
        os.makedirs(folder, exist_ok=True)
        if file.filename is None:
            raise MessageException('Nie można zapisać pliku')
        filename = secure_filename(file.filename)
        path = os.path.join(folder, filename)
        try:
            file.save(path)
            return path
        except Exception as e:
            raise MessageException.from_exception(e, 'Nie można zapisać pliku')

    @staticmethod
    def extract_tex_files_from_archive(file: FileStorage, folder: str) -> list[str]:
        os.makedirs(folder, exist_ok=True)
        archive_path = LatexService.save_file(file, folder)
        if file.filename is None:
            raise MessageException('Nie można rozpakować plików')
        ext = os.path.splitext(file.filename)[1].lower()
        tex_files = []

        try:
            if ext == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    archive.extractall(folder)
                    print(archive.namelist())
                    tex_files = [
                        os.path.join(folder, name)
                        for name in archive.namelist()
                        if name.endswith('.tex')
                    ]
            elif ext in {'.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2'}:
                with tarfile.open(archive_path, 'r:*') as archive:
                    archive.extractall(folder)
                    print(archive.getnames())
                    tex_files = [
                        os.path.join(folder, name)
                        for name in archive.getnames()
                        if name.endswith('.tex')
                    ]
            else:
                raise MessageException(
                    'Nie można rozpakować plików',
                    err=Exception('Nieznane rozszerzenie archiwum')
                )

            return tex_files
        except Exception as e:
            raise MessageException.from_exception(e, 'Nie można rozpakować plików')

    @staticmethod
    def is_safe_tex(tex_path: str, allowed_folder: str) -> bool:
        forbidden_patterns = [
            r"\\immediate\s*\\write18",
            r"\\csname\s*write18\s*\\endcsname",
            r"\\expandafter\s*\\immediate\s*\\csname\s*write18\s*\\endcsname",
            r"\\def\s*\w+\s*\{.*?write18.*?\}",
            r"\\edef\s*\w+\s*\{.*?write18.*?\}",
        ]

        dangerous_paths = ["/etc/", "/root/", "/home/user/.ssh/", "/var/www/"]
        shell_commands = [
            r"cat\s+", r"rm\s+", r"wget\s+", r"curl\s+",
            r"python\s+-c", r"nc\s+", r"bash\s+-c", r"sh\s+-c",
            r"chmod\s+", r"mv\s+", r"scp\s+", r"ssh\s+"
        ]

        try:
            with open(tex_path, "r", encoding="utf-8") as f:
                content = f.readlines()

            for line in content:
                stripped_line = line.strip()
                if stripped_line.startswith("%"):
                    continue

                for pattern in forbidden_patterns:
                    if re.search(pattern, stripped_line):
                        raise MessageException(f"❌ Niedozwolony kod LaTeX: `{stripped_line}`")

                for pattern in shell_commands:
                    if re.search(pattern, stripped_line):
                        raise MessageException(f"❌ Podejrzana komenda shell w LaTeX: `{stripped_line}`")

                openout_immediate_match = re.search(r"\\immediate\s*\\openout\s*\w+\s*=\s*\"?([^\"}]+)\"?", stripped_line)
                if openout_immediate_match:
                    file_path = openout_immediate_match.group(1).strip().replace('"', '')
                    abs_path = os.path.abspath(os.path.join(os.path.dirname(tex_path), file_path))
                    if "#" in file_path or "\\" in file_path or file_path.startswith(("~", ".", "..")):
                        raise MessageException(f"❌ `\\openout` używa niedozwolonej ścieżki: `{file_path}`")
                    for forbidden_path in dangerous_paths:
                        if abs_path.startswith(forbidden_path):
                            raise MessageException(f"❌ `\\openout` próbuje pisać do zabronionej ścieżki: `{file_path}`")

                if "\\usepackage{minted}" in stripped_line:
                    for full_line in content:
                        if "\\inputminted" in full_line:
                            raise MessageException(
                                "❌ Użycie `inputminted` z pakietem `minted` wymaga `--shell-escape`, co jest niedozwolone!")

                write_match = re.search(r"\\write\s*\d+\s*\{(.+?)\}", stripped_line)
                if write_match:
                    write_content = write_match.group(1).strip()
                    for pattern in shell_commands:
                        if re.search(pattern, write_content):
                            raise MessageException(f"❌ `\\write` zawiera niebezpieczne polecenie: `{write_content}`")

                input_match = re.search(r"\\(input|include)(?:\[[^\]]*\])?\{([^}]+)\}", stripped_line)
                if input_match:
                    included_file = input_match.group(2).strip()
                    abs_path = os.path.abspath(os.path.join(os.path.dirname(tex_path), included_file))
                    if not abs_path.startswith(os.path.abspath(allowed_folder)):
                        raise MessageException(f"❌ `\\{input_match.group(1)}` odwołuje się do pliku poza dozwoloną ścieżką: `{included_file}`")
                    if not os.path.exists(abs_path):
                        raise MessageException(f"❌ Plik dołączany przez `\\{input_match.group(1)}` nie istnieje: `{included_file}`")

                lst_match = re.search(r"\\lstinputlisting(?:\[[^\]]*\])?\{([^}]+)\}", stripped_line)
                if lst_match:
                    listing_file = lst_match.group(1).strip()
                    abs_path = os.path.abspath(os.path.join(os.path.dirname(tex_path), listing_file))
                    if not abs_path.startswith(os.path.abspath(allowed_folder)):
                        raise MessageException(f"❌ `\\lstinputlisting` próbuje wczytać plik spoza folderu: `{listing_file}`")
                    if not os.path.exists(abs_path):
                        raise MessageException(f"❌ Plik `\\lstinputlisting` nie istnieje: `{listing_file}`")

            full_text = "".join(content)
            match = re.search(r"\\begin{document}(.*?)\\end{document}", full_text, re.DOTALL)
            if not match:
                raise MessageException("❌ Brakuje \\begin{document} lub \\end{document} – niepoprawny plik LaTeX.")
            if not match.group(1).strip():
                raise MessageException("❌ Dokument LaTeX jest pusty – brak treści do kompilacji.")

            return True

        except MessageException:
            raise
        except Exception as e:
            raise MessageException(f"❌ Błąd analizy bezpieczeństwa LaTeX: {str(e)}")
