"""
MCP 工具处理器模块

提供 check_abap_syntax 工具的处理逻辑，包括输入验证、RFC 调用、
结果格式化和错误处理。
"""

import logging
from typing import Dict, Any, Optional
from src.models import CheckResult
from src.rfc_client import RFCClient, RFCConnectionError, RFCCallError


logger = logging.getLogger(__name__)


class ToolHandlerError(Exception):
    """工具处理器错误基类"""
    pass


class InputValidationError(ToolHandlerError):
    """输入参数验证错误"""
    pass


class ToolHandler:
    """
    MCP 工具处理器
    
    处理 check_abap_syntax 工具的调用，包括参数验证、RFC 调用和结果格式化。
    """
    
    # RFC 函数模块名称
    RFC_FUNCTION_NAME = "Z_CHECK_ABAP_SYNTAX"
    
    # 代码长度限制（行数）
    MAX_CODE_LINES = 10000
    
    def __init__(self, rfc_client: RFCClient):
        """
        初始化工具处理器
        
        Args:
            rfc_client: RFC 客户端实例
        """
        self.rfc_client = rfc_client
    
    def validate_input(self, code: Optional[str]) -> None:
        """
        验证输入参数
        
        Args:
            code: ABAP 代码字符串
            
        Raises:
            InputValidationError: 当输入参数无效时
        """
        # 检查 code 参数是否存在
        if code is None:
            raise InputValidationError("缺少必需参数: 'code'")
        
        # 检查 code 是否为字符串
        if not isinstance(code, str):
            raise InputValidationError(
                f"参数 'code' 必须是字符串类型，当前类型: {type(code).__name__}"
            )
        
        # 检查 code 是否为空
        if not code.strip():
            raise InputValidationError("参数 'code' 不能为空")
        
        # 检查代码长度
        line_count = len(code.splitlines())
        if line_count > self.MAX_CODE_LINES:
            raise InputValidationError(
                f"代码行数超过限制: {line_count} > {self.MAX_CODE_LINES}"
            )
        
        logger.debug(f"输入验证通过，代码行数: {line_count}")
    
    def check_abap_syntax(self, code: str) -> CheckResult:
        """
        执行 ABAP 语法检查
        
        Args:
            code: ABAP REPORT 程序源代码
            
        Returns:
            CheckResult: 语法检查结果
            
        Raises:
            InputValidationError: 当输入参数无效时
            RFCConnectionError: 当 RFC 连接失败时
            RFCCallError: 当 RFC 函数调用失败时
        """
        # 验证输入参数
        self.validate_input(code)
        
        logger.info(f"开始执行 ABAP 语法检查，代码长度: {len(code)} 字符")
        
        try:
            # 确保 RFC 连接已建立
            if not self.rfc_client.is_connected:
                logger.info("RFC 连接未建立，正在建立连接")
                self.rfc_client.connect()
            
            # 调用 RFC 函数模块
            response = self.rfc_client.call_function(
                self.RFC_FUNCTION_NAME,
                IV_CODE=code
            )
            
            # 解析响应为 CheckResult
            result = CheckResult.from_rfc_response(response)
            
            # 记录检查结果摘要
            if result.success:
                if result.has_errors:
                    logger.info(
                        f"语法检查完成，发现 {len(result.errors)} 个问题"
                    )
                else:
                    logger.info("语法检查完成，代码无错误")
            else:
                logger.warning(f"语法检查执行失败: {result.message}")
            
            return result
            
        except (RFCConnectionError, RFCCallError) as e:
            # RFC 相关错误直接向上传播
            logger.error(f"RFC 调用失败: {str(e)}")
            raise
        
        except Exception as e:
            # 其他未预期的错误
            error_msg = f"语法检查过程中发生未预期错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ToolHandlerError(error_msg) from e
    
    def format_mcp_response(self, result: CheckResult) -> Dict[str, Any]:
        """
        格式化为 MCP 响应格式
        
        Args:
            result: 语法检查结果
            
        Returns:
            Dict[str, Any]: MCP 响应对象
        """
        return {
            "content": [
                {
                    "type": "text",
                    "text": result.to_json()
                }
            ]
        }
    
    def format_error_response(
        self, 
        error_code: str, 
        error_message: str
    ) -> Dict[str, Any]:
        """
        格式化错误响应
        
        Args:
            error_code: 错误代码
            error_message: 错误消息
            
        Returns:
            Dict[str, Any]: MCP 错误响应对象
        """
        return {
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
    
    def handle_check_syntax(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 check_abap_syntax 工具调用
        
        这是主要的入口点，处理完整的工具调用流程，包括：
        1. 提取参数
        2. 执行语法检查
        3. 格式化响应
        4. 错误处理
        
        Args:
            arguments: 工具调用参数字典
            
        Returns:
            Dict[str, Any]: MCP 响应（成功或错误）
        """
        try:
            # 提取 code 参数
            code = arguments.get("code")
            
            # 执行语法检查
            result = self.check_abap_syntax(code)
            
            # 格式化为 MCP 响应
            return self.format_mcp_response(result)
            
        except InputValidationError as e:
            # 输入验证错误
            logger.warning(f"输入验证失败: {str(e)}")
            return self.format_error_response(
                "INVALID_INPUT",
                str(e)
            )
        
        except RFCConnectionError as e:
            # RFC 连接错误
            logger.error(f"RFC 连接失败: {str(e)}")
            return self.format_error_response(
                "CONNECTION_FAILED",
                f"无法连接到 ERP 系统: {str(e)}"
            )
        
        except RFCCallError as e:
            # RFC 调用错误
            logger.error(f"RFC 函数调用失败: {str(e)}")
            return self.format_error_response(
                "RFC_CALL_FAILED",
                f"调用语法检查函数失败: {str(e)}"
            )
        
        except ToolHandlerError as e:
            # 工具处理器错误
            logger.error(f"工具处理器错误: {str(e)}")
            return self.format_error_response(
                "TOOL_HANDLER_ERROR",
                str(e)
            )
        
        except Exception as e:
            # 未预期的错误
            logger.error(f"处理工具调用时发生未预期错误: {str(e)}", exc_info=True)
            return self.format_error_response(
                "INTERNAL_ERROR",
                f"内部错误: {str(e)}"
            )
