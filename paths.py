import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
APP_ICON_ICO = os.path.join(ASSETS_DIR, "app_icon.ico")
APP_LOGO_PNG = os.path.join(ASSETS_DIR, "logo.png")

APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ProjectVault")
os.makedirs(APPDATA_DIR, exist_ok=True)

PROJECTS_DB_PATH = os.path.join(APPDATA_DIR, "projects_metadata.json")
CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")
DEFAULT_PROJECTS_DIR = r"C:\Users\admin\Desktop\VS Codes\Projects"
