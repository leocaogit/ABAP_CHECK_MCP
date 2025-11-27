"""
日志记录模块

提供结构化日志配置，包括敏感信息过滤和多输出目标支持。
"""

import logging
import sys
import re
from typing import Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SensitiveDataFilter(logging.Filter):
    """
    敏感信息过滤器
    
    在日志输出前屏蔽密码等敏感信息。
    """
    
    # 需要屏蔽的字段名称（不区分大小写）
    SENSITIVE_FIELDS = [
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey'
    ]
    
    # 屏蔽替换文本
    MASK = '***MASKED***'
    
    def __init__(self):
        super().__init__()
        # 编译正则表达式以提高性能
        # 匹配模式: field_name=value 或 field_name: value 或 "field_name": "value"
        patterns = []
        for field in self.SENSITIVE_FIELDS:
            # 匹配 key=value 格式（如 password=secret123）
            patterns.append(
                rf'\b{field}\s*=\s*["\']?([^\s,}}\]"\']+ )["\']?'
            )
            # 匹配 JSON 格式 "key": "value"
            patterns.append(
                rf'"{field}"\s*:\s*"([^"]*)"'
            )
            # 匹配 JSON 格式 'key': 'value'
            patterns.append(
                rf"'{field}'\s*:\s*'([^']*)'"
            )
        
        self.pattern = re.compile('|'.join(patterns), re.IGNORECASE)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录，屏蔽敏感信息
        
        Args:
            record: 日志记录对象
            
        Returns:
            bool: 始终返回 True（不阻止日志输出）
        """
        # 屏蔽消息中的敏感信息
        if isinstance(record.msg, str):
            record.msg = self._mask_sensitive_data(record.msg)
        
        # 屏蔽参数中的敏感信息
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_if_sensitive(k, v) 
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """
        屏蔽文本中的敏感数据
        
        Args:
            text: 原始文本
            
        Returns:
            str: 屏蔽后的文本
        """
        def replace_match(match):
            # 获取完整匹配的文本
            full_match = match.group(0)
            # 找到值的部分（第一个非 None 的捕获组）
            for group in match.groups():
                if group is not None:
                    # 替换值部分为 MASK
                    return full_match.replace(group, self.MASK)
            return self.MASK
        
        return self.pattern.sub(replace_match, text)
    
    def _mask_if_sensitive(self, key: str, value: any) -> any:
        """
        如果键名是敏感字段，则屏蔽值
        
        Args:
            key: 字段名
            value: 字段值
            
        Returns:
            any: 原值或屏蔽后的值
        """
        if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
            return self.MASK
        return value


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器
    
    提供包含时间戳、级别、模块、消息的结构化日志格式。
    """
    
    def __init__(self):
        # 格式: 时间戳 | 级别 | 模块:行号 | 消息
        fmt = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            str: 格式化后的日志字符串
        """
        # 为不同级别添加颜色（仅用于控制台输出）
        if hasattr(record, 'use_color') and record.use_color:
            levelname = record.levelname
            if levelname == 'DEBUG':
                record.levelname = f'\033[36m{levelname}\033[0m'  # 青色
            elif levelname == 'INFO':
                record.levelname = f'\033[32m{levelname}\033[0m'  # 绿色
            elif levelname == 'WARNING':
                record.levelname = f'\033[33m{levelname}\033[0m'  # 黄色
            elif levelname == 'ERROR':
                record.levelname = f'\033[31m{levelname}\033[0m'  # 红色
            elif levelname == 'CRITICAL':
                record.levelname = f'\033[35m{levelname}\033[0m'  # 紫色
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_color: bool = True
) -> None:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件名（可选，如果为 None 则不输出到文件）
        log_dir: 日志文件目录
        max_bytes: 单个日志文件最大字节数（用于日志轮转）
        backup_count: 保留的日志文件备份数量
        enable_console: 是否启用控制台输出
        enable_color: 是否在控制台输出中启用颜色
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)
    
    # 清除现有的处理器（避免重复配置）
    root_logger.handlers.clear()
    
    # 创建敏感信息过滤器
    sensitive_filter = SensitiveDataFilter()
    
    # 配置控制台输出
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 创建格式化器
        console_formatter = StructuredFormatter()
        console_handler.setFormatter(console_formatter)
        
        # 添加敏感信息过滤器
        console_handler.addFilter(sensitive_filter)
        
        # 为控制台处理器添加颜色标记
        if enable_color:
            class ColorFilter(logging.Filter):
                def filter(self, record):
                    record.use_color = True
                    return True
            console_handler.addFilter(ColorFilter())
        
        root_logger.addHandler(console_handler)
    
    # 配置文件输出
    if log_file:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建文件处理器（带日志轮转）
        file_path = log_path / log_file
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # 创建格式化器（文件输出不使用颜色）
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        
        # 添加敏感信息过滤器
        file_handler.addFilter(sensitive_filter)
        
        root_logger.addHandler(file_handler)
    
    # 记录日志系统初始化信息
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成，级别: {log_level}")
    if log_file:
        logger.info(f"日志文件: {log_dir}/{log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常使用 __name__）
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)
