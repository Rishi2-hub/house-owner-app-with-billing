from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def get_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def backup_db(db_path="data/app.db"):
    drive = get_drive()

    file = drive.CreateFile({"title": "ghar_saathi_backup.db"})
    file.SetContentFile(db_path)
    file.Upload()

    return file["id"]