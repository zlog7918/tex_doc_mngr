import os
import tarfile
import zipfile
import subprocess
from flask import send_from_directory
from werkzeug.utils import secure_filename
from models.utils.Response import Response
from werkzeug.datastructures import FileStorage

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
    def save_file(file: FileStorage, folder: str) -> str:
        os.makedirs(folder, exist_ok=True)
        filename = secure_filename(file.filename)
        path = os.path.join(folder, filename)

        try:
            file.save(path)
        except Exception:
            pass

        return path

    @staticmethod
    def extract_tex_files_from_archive(file: FileStorage, folder: str) -> list[str]:
        os.makedirs(folder, exist_ok=True)
        archive_path = LatexService.save_file(file, folder)
        ext = os.path.splitext(file.filename)[1].lower()
        tex_files = []

        try:
            if ext == ".zip":
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    archive.extractall(folder)
                    tex_files = [
                        os.path.join(folder, name)
                        for name in archive.namelist()
                        if name.endswith('.tex')
                    ]
            elif ext in [".tar", ".gz", ".bz2", ".xz", ".tgz", ".tbz2"]:
                with tarfile.open(archive_path, 'r:*') as archive:
                    archive.extractall(folder)
                    tex_files = [
                        os.path.join(folder, name)
                        for name in archive.getnames()
                        if name.endswith('.tex')
                    ]
            else:
                pass

        except Exception:
            pass

        return tex_files

