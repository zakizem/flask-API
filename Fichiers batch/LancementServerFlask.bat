:: Remplacer le r�pertoire : C:/Users/zzr/flask_projets/git_repo/API par le r�pertoire contenant l'API dans votre machine

CALL C:/Users/zzr/flask_projets/git_repo/API/venv\Scripts\activate.bat
cd C:/Users/zzr/flask_projets/git_repo/API/venv/app
set FLASK_APP=app.py
set FLASK_DEBUG=1
flask run --with-threads --port 8011
