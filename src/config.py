"""
配置管理模块

提供从环境变量和 JSON 文件读取配置的功能，并验证配置完整性。
"""

import os
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class RFCConfig:
    """RFC 连接配置"""
    host: str
    sysnr: str
    client: str
    user: str
    password: str
    saprouter: Optional[str] = None  # SAProuter 字符串，例如: "/H/saprouter.example.com/S/3299/H/"

    def validate(self) -> None:
        """
        验证配置完整性，检查必需字段
        
        Raises:
            ValueError: 当必需字段缺失或为空时
        """
        required_fields = {
            'host': self.host,
            'sysnr': self.sysnr,
            'client': self.client,
            'user': self.user,
            'password': self.password
        }
        
        missing_fields = []
        for field_name, field_value in required_fields.items():
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ValueError(
                f"缺少必需的配置参数: {', '.join(missing_fields)}"
            )


@dataclass
class Config:
    """MCP 服务器配置"""
    rfc: RFCConfig
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """
        从环境变量读取配置
        
        环境变量:
            SAP_HOST: SAP 系统主机名
            SAP_SYSNR: SAP 系统号
            SAP_CLIENT: SAP 客户端
            SAP_USER: SAP 用户名
            SAP_PASSWORD: SAP 密码
            LOG_LEVEL: 日志级别 (可选，默认 INFO)
        
        Returns:
            Config: 配置对象
            
        Raises:
            ValueError: 当必需的环境变量缺失时
        """
        rfc_config = RFCConfig(
            host=os.getenv('SAP_HOST', ''),
            sysnr=os.getenv('SAP_SYSNR', ''),
            client=os.getenv('SAP_CLIENT', ''),
            user=os.getenv('SAP_USER', ''),
            password=os.getenv('SAP_PASSWORD', ''),
            saprouter=os.getenv('SAP_ROUTER')  # 可选的 SAProuter 配置
        )
        
        # 验证配置
        rfc_config.validate()
        
        return cls(
            rfc=rfc_config,
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """
        从 JSON 文件读取配置
        
        Args:
            path: JSON 配置文件路径
            
        Returns:
            Config: 配置对象
            
        Raises:
            FileNotFoundError: 当配置文件不存在时
            ValueError: 当配置文件格式错误或必需字段缺失时
            json.JSONDecodeError: 当 JSON 格式无效时
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查必需的顶层字段
        if 'rfc' not in data:
            raise ValueError("配置文件缺少 'rfc' 字段")
        
        rfc_data = data['rfc']
        rfc_config = RFCConfig(
            host=rfc_data.get('host', ''),
            sysnr=rfc_data.get('sysnr', ''),
            client=rfc_data.get('client', ''),
            user=rfc_data.get('user', ''),
            password=rfc_data.get('password', ''),
            saprouter=rfc_data.get('saprouter')  # 可选的 SAProuter 配置
        )
        
        # 验证配置
        rfc_config.validate()
        
        return cls(
            rfc=rfc_config,
            log_level=data.get('log_level', 'INFO')
        )

    def validate(self) -> None:
        """
        验证整个配置的完整性
        
        Raises:
            ValueError: 当配置无效时
        """
        self.rfc.validate()
