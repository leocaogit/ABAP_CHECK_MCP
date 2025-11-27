"""
RFC 客户端模块

提供与 SAP ERP 系统的 RFC 连接管理和函数调用功能。
"""

import logging
from typing import Optional, Dict, Any

try:
    from pyrfc import Connection, ABAPApplicationError, ABAPRuntimeError, LogonError, CommunicationError
    PYRFC_AVAILABLE = True
except ImportError:
    # pyrfc not available - define placeholder classes for type checking
    PYRFC_AVAILABLE = False
    Connection = None
    ABAPApplicationError = Exception
    ABAPRuntimeError = Exception
    LogonError = Exception
    CommunicationError = Exception

from src.config import RFCConfig


logger = logging.getLogger(__name__)


class RFCConnectionError(Exception):
    """RFC 连接错误"""
    pass


class RFCCallError(Exception):
    """RFC 函数调用错误"""
    pass


class RFCClient:
    """
    RFC 客户端类
    
    管理与 SAP ERP 系统的 RFC 连接，提供函数调用接口。
    """
    
    def __init__(self, config: RFCConfig):
        """
        初始化 RFC 客户端
        
        Args:
            config: RFC 连接配置
        """
        self.config = config
        self._connection: Optional[Connection] = None
        self._is_connected = False
    
    def connect(self):
        """
        建立与 ERP 系统的 RFC 连接
        
        Returns:
            Connection: pyrfc 连接对象
            
        Raises:
            RFCConnectionError: 当连接失败时
        """
        if not PYRFC_AVAILABLE:
            raise RFCConnectionError(
                "pyrfc 库未安装。请安装 SAP NetWeaver RFC SDK 和 pyrfc 库。"
            )
        
        if self._is_connected and self._connection:
            logger.debug("RFC 连接已存在，重用现有连接")
            return self._connection
        
        try:
            # 构建连接参数
            conn_params = {
                'ashost': self.config.host,
                'sysnr': self.config.sysnr,
                'client': self.config.client,
                'user': self.config.user,
                'passwd': self.config.password
            }
            
            # 如果配置了 SAProuter，添加到连接参数
            if self.config.saprouter:
                conn_params['saprouter'] = self.config.saprouter
                logger.info(
                    f"正在通过 SAProuter 连接到 SAP 系统: {self.config.saprouter} -> "
                    f"{self.config.host}:{self.config.sysnr} "
                    f"(客户端: {self.config.client}, 用户: {self.config.user})"
                )
            else:
                logger.info(
                    f"正在连接到 SAP 系统: {self.config.host}:{self.config.sysnr} "
                    f"(客户端: {self.config.client}, 用户: {self.config.user})"
                )
            
            # 创建 RFC 连接
            self._connection = Connection(**conn_params)
            
            self._is_connected = True
            logger.info("RFC 连接建立成功")
            
            return self._connection
            
        except LogonError as e:
            error_msg = f"RFC 登录失败: {str(e)}"
            logger.error(error_msg)
            raise RFCConnectionError(error_msg) from e
            
        except CommunicationError as e:
            error_msg = f"RFC 通信错误: {str(e)}"
            logger.error(error_msg)
            raise RFCConnectionError(error_msg) from e
            
        except Exception as e:
            error_msg = f"RFC 连接失败: {str(e)}"
            logger.error(error_msg)
            raise RFCConnectionError(error_msg) from e
    
    def call_function(self, function_name: str, **params: Any) -> Dict[str, Any]:
        """
        调用远程函数模块
        
        Args:
            function_name: 函数模块名称
            **params: 函数参数（导入参数和表参数）
            
        Returns:
            Dict[str, Any]: 函数返回结果（导出参数和表参数）
            
        Raises:
            RFCConnectionError: 当连接未建立时
            RFCCallError: 当函数调用失败时
        """
        if not self._is_connected or not self._connection:
            raise RFCConnectionError("RFC 连接未建立，请先调用 connect()")
        
        try:
            logger.debug(f"调用 RFC 函数: {function_name}")
            logger.debug(f"函数参数: {self._sanitize_params(params)}")
            
            # 调用远程函数
            result = self._connection.call(function_name, **params)
            
            logger.debug(f"函数调用成功，返回结果: {self._sanitize_result(result)}")
            
            return result
            
        except ABAPApplicationError as e:
            error_msg = f"ABAP 应用错误: {e.key} - {e.message}"
            logger.error(error_msg)
            raise RFCCallError(error_msg) from e
            
        except ABAPRuntimeError as e:
            error_msg = f"ABAP 运行时错误: {str(e)}"
            logger.error(error_msg)
            raise RFCCallError(error_msg) from e
            
        except CommunicationError as e:
            error_msg = f"RFC 通信错误: {str(e)}"
            logger.error(error_msg)
            self._is_connected = False
            raise RFCConnectionError(error_msg) from e
            
        except Exception as e:
            error_msg = f"RFC 函数调用失败: {str(e)}"
            logger.error(error_msg)
            raise RFCCallError(error_msg) from e
    
    def disconnect(self) -> None:
        """
        关闭 RFC 连接
        """
        if self._connection and self._is_connected:
            try:
                logger.info("正在关闭 RFC 连接")
                self._connection.close()
                self._is_connected = False
                self._connection = None
                logger.info("RFC 连接已关闭")
            except Exception as e:
                logger.error(f"关闭 RFC 连接时发生错误: {str(e)}")
                # 即使关闭失败，也标记为未连接
                self._is_connected = False
                self._connection = None
        else:
            logger.debug("RFC 连接未建立，无需关闭")
    
    @property
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 是否已连接
        """
        return self._is_connected and self._connection is not None
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理参数中的敏感信息用于日志记录
        
        Args:
            params: 原始参数
            
        Returns:
            Dict[str, Any]: 清理后的参数
        """
        sanitized = {}
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 100:
                sanitized[key] = f"{value[:100]}... (长度: {len(value)})"
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理结果中的敏感信息用于日志记录
        
        Args:
            result: 原始结果
            
        Returns:
            Dict[str, Any]: 清理后的结果
        """
        sanitized = {}
        for key, value in result.items():
            if isinstance(value, list) and len(value) > 10:
                sanitized[key] = f"[列表，长度: {len(value)}]"
            elif isinstance(value, str) and len(value) > 200:
                sanitized[key] = f"{value[:200]}... (长度: {len(value)})"
            else:
                sanitized[key] = value
        return sanitized
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
        return False
