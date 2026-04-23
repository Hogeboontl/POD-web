import os, re, hashlib
from app.settings.settings import upload_dir
#sanitizes user email and then adds small end hash to prevent non uniqueness
def get_user_dir(email, upload_dir = upload_dir):
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", email.split("@")[0])
    email_hash = hashlib.sha1(email.encode()).hexdigest()[:8]
    folder_name = f"{safe_name}_{email_hash}"
    user_dir = os.path.join(upload_dir, folder_name)
    os.makedirs(user_dir, exist_ok=True)
    os.chmod(user_dir, 0o2775)
    return user_dir