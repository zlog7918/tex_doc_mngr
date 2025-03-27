import os
import subprocess
import tempfile
import tarfile
import zipfile
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import send_from_directory
from models.utils.Response import Response
from models.utils.utils import get_temp_folder, get_upload_folder

class LatexService:
    @staticmethod
    def convert_tex_to_pdf(tex_path: str, output_dir: str) -> bool:
        try:
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "--shell-escape", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                    cwd=output_dir,
                    check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                print("[📄 PDFLaTeX STDOUT]", result.stdout.decode())
                print("[❗ PDFLaTeX STDERR]", result.stderr.decode())

            pdf_path = tex_path.replace('.tex', '.pdf')
            return os.path.exists(pdf_path)
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def generate_preview(tex_path: str) -> Response:
        temp_folder = os.path.dirname(tex_path)
        filename = os.path.basename(tex_path)
        if LatexService.convert_tex_to_pdf(tex_path, temp_folder):
            return Response.success_response(data={
                "pdf_url": f"/articles/temp-preview/{filename.replace('.tex', '.pdf')}"
            })
        else:
            return Response.error_response(message="Błąd generowania PDF")

    @staticmethod
    def get_file(folder: str, filename: str) -> Response:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            return Response.success_response(send_from_directory(folder, filename))
        return Response.error_response(message="Plik nie istnieje")

    @staticmethod
    def get_uploaded_file(filename: str) -> Response:
        return LatexService.get_file(get_upload_folder(), filename)

    @staticmethod
    def get_temp_preview(filename: str) -> Response:
        return LatexService.get_file(get_temp_folder(), filename)

    @staticmethod
    def save_file(file: FileStorage, folder: str) -> str:
        os.makedirs(folder, exist_ok=True)
        filename = secure_filename(file.filename)
        path = os.path.join(folder, filename)
        file.save(path)
        return path

    @staticmethod
    def extract_archive_and_find_tex(file: FileStorage, folder: str) -> str | None:
        os.makedirs(folder, exist_ok=True)
        archive_path = LatexService.save_file(file, folder)
        ext = os.path.splitext(file.filename)[1].lower()
        tex_file = None

        try:
            if ext == ".zip":
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    archive.extractall(folder)
                    files = archive.namelist()

            elif ext in [".tar", ".gz", ".bz2", ".xz", ".tgz", ".tbz2"]:
                with tarfile.open(archive_path, 'r:*') as archive:
                    archive.extractall(folder)
                    files = archive.getnames()

            else:
                return None

            for name in files:
                if name.endswith('.tex') and not tex_file:
                    tex_file = os.path.join(folder, name)

        except Exception:
            return None

        return tex_file
