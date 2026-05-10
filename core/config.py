import json
import os
import sys
from pathlib import Path


DEFAULTS = {
    'page_size': 'A4',
    'orientation': 'portrait',
    'margin': 72,
    'quality': 'original',
    'parallel_mode': 'auto',
    'theme': 'light',
}


def _get_config_path():
    """获取配置文件路径：exe所在目录（打包后）或项目根目录（开发时）"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    return base / "config.json"


def load_config():
    """加载配置，文件不存在或损坏时返回默认值"""
    path = _get_config_path()
    config = dict(DEFAULTS)
    try:
        with open(str(path), 'r', encoding='utf-8') as f:
            saved = json.load(f)
            config.update(saved)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return config


def save_config(config):
    """保存配置到文件"""
    path = _get_config_path()
    try:
        with open(str(path), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
