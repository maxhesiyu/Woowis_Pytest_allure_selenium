import logging
import colorlog

import time

from config.config import LOG_DIR

# 创建日志器
log = logging.getLogger('auto_test')
log.setLevel(logging.DEBUG)

# 避免重复添加处理器
if not log.handlers:
    # 文件处理器（按天生成）
    daytime = time.strftime('%Y-%m-%d')
    file_path = LOG_DIR / f"run_log_{daytime}.log"
    file_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        fmt='[%(levelname)s] [%(asctime)s.%(msecs)03d] : %(message)s -> %(funcName)s line:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # 控制台处理器（带颜色）
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = colorlog.ColoredFormatter(
        fmt='[%(log_color)s%(levelname)s] [%(asctime)s] : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={'DEBUG': 'white', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red'}
    )
    console_handler.setFormatter(console_formatter)

    # 添加处理器
    log.addHandler(file_handler)
    log.addHandler(console_handler)