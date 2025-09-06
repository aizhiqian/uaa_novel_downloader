import os
import sys
from pathlib import Path
import json
from dotenv import load_dotenv

class Config:
    """配置管理类"""
    # 加载根目录下的 .env 文件
    ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(ROOT_DIR / ".env")

    # 基础URL和网站信息
    BASE_URL = "https://www.uaa001.com"
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'

    # 目录配置
    CONFIG_DIR = ROOT_DIR / "config"
    DATA_DIR = ROOT_DIR / "data"
    LOGS_DIR = ROOT_DIR / "logs"
    OUTPUT_DIR = ROOT_DIR / "output"

    # ChromeDriver管理配置
    WEBDRIVER_CACHE_DIR = ROOT_DIR / ".wdm"

    # 文件配置
    COOKIE_FILE = DATA_DIR / "cookies.json"
    USERS_FILE = CONFIG_DIR / "users.txt"
    PROGRESS_FILE = DATA_DIR / "progress.json"
    CHROMEDRIVER_PATH = ROOT_DIR / "chromedriver.exe"

    # 网络请求配置
    RETRY_COUNT = 3
    RETRY_DELAY = 5
    CHAPTER_DELAY = 5

    # 浏览器配置
    CHROME_OPTIONS = {
        "headless": True,
        "disable_gpu": True,
        "window_size": "1920,1080",
        "start_maximized": True,
        "incognito": True,
        "no_sandbox": True,
        "disable_dev_shm_usage": True,
        "ignore_certificate_errors": True,
        "ignore_ssl_errors": True,
        "allow_insecure_localhost": True,
        "disable_web_security": True,
        "enable-unsafe-swiftshader": True,
        "log_level": 3,
        "silent": True,
        "disable-gpu-compositing": True,
        "disable_background_networking": True,
        "disable_background_timer_throttling": True,
        "disable_renderer_backgrounding": True,
        "disable_backgrounding_occluded_windows": True,
        "disable_component_extensions_with_background_pages": True,
        "disable_ipc_flooding_protection": True,
        "disable_sync": True,
        "metrics_recording_only": True,
        "no_first_run": True,
        "disable_default_apps": True,
        "disable_extensions": True,
        "disable_plugins": True,
        "disable_popup_blocking": True,
        "disable_prompt_on_repost": True,
        "disable_hang_monitor": True,
        "disable_client_side_phishing_detection": True,
        "disable_component_update": True,
        "disable_domain_reliability": True,
        "disable_features": "VizDisplayCompositor,TranslateUI,GCMRegistration",
        "gcm_registration_enabled": False,
        "disable_gcm_registration": True,
        "disable_google_apis": True,
        "disable_cloud_import": True,
        "disable_google_apis_registration": True,
        "gcm_disabled": True,
    }

    # AI识别验证码配置
    AI_API_BASE_URL = os.getenv("AI_API_BASE_URL")
    AI_API_KEY = os.getenv("AI_API_KEY")  # 请在此处填入您的API KEY
    AI_MODEL = os.getenv("AI_MODEL")  # 使用支持视觉的模型

def setup_directories():
    """创建必要的目录结构"""
    directories = [
        Config.CONFIG_DIR,
        Config.DATA_DIR,
        Config.LOGS_DIR,
        Config.OUTPUT_DIR
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # 创建默认的users.txt文件
    if not Config.USERS_FILE.exists():
        with open(Config.USERS_FILE, 'w', encoding='utf-8') as f:
            f.write("# 账号配置文件，每行一个账号，格式为：编号. 邮箱 密码\n")
            f.write("# 例如：1. example@mail.com password123\n")

    # 创建默认的进度文件
    if not Config.PROGRESS_FILE.exists():
        with open(Config.PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
