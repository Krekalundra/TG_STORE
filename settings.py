ALLOWED_HOSTS = ['158.255.6.226', 'django146299.hostkey.in', 'localhost']
INSTALLED_APPS = [
    "admin_interface",
    "colorfield",  # именно так
    "django.contrib.admin",
    "TG_STORE"
    # ... остальные приложения ...
]
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]
