import logging
import os
from pathlib import Path
from datetime import datetime
from .config import Config

def setup_logger(name):
    """设置日志记录器"""
    # 确保日志目录存在
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 创建日志文件名（包含日期）
    log_file = Config.LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    # 配置日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 如果已经有处理器，不再添加新处理器
    if logger.handlers:
        return logger

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器（可选）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # 只在控制台显示错误

    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
