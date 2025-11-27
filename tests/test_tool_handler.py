"""
单元测试：MCP 工具处理器

测试 tool_handler 模块的输入验证、结果格式化和错误处理功能。
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.tool_handler import ToolHandler, InputValidationError, ToolHandlerError
from src.models import CheckResult, SyntaxError
from src.rfc_client import RFCConnectionError, RFCCallError


class TestInputValidation:
    """测试输入参数验证"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_rfc_client = Mock()
        self.handler = ToolHandler(self.mock_rfc_client)
    
    def test_validate_input_with_valid_code(self):
        """测试有效代码通过验证"""
        code = "REPORT test.\nWRITE 'Hello'."
        # 不应抛出异常
        self.handler.validate_input(code)
    
    def test_validate_input_with_none(self):
        """测试 None 参数被拒绝"""
        with pytest.raises(InputValidationError) as exc_info:
            self.handler.validate_input(None)
        assert "缺少必需参数" in str(exc_info.value)
    
    def test_validate_input_with_empty_string(self):
        """测试空字符串被拒绝"""
        with pytest.raises(InputValidationError) as exc_info:
            self.handler.validate_input("")
        assert "不能为空" in str(exc_info.value)
    
    def test_validate_input_with_whitespace_only(self):
        """测试仅包含空白字符的字符串被拒绝"""
        with pytest.raises(InputValidationError) as exc_info:
            self.handler.validate_input("   \n\t  ")
        assert "不能为空" in str(exc_info.value)
    
    def test_validate_input_with_non_string(self):
        """测试非字符串类型被拒绝"""
        with pytest.raises(InputValidationError) as exc_info:
            self.handler.validate_input(123)
        assert "必须是字符串类型" in str(exc_info.value)
    
    def test_validate_input_with_too_many_lines(self):
        """测试超长代码被拒绝"""
        # 创建超过限制的代码
        code = "\n".join([f"WRITE '{i}'." for i in range(10001)])
        with pytest.raises(InputValidationError) as exc_info:
            self.handler.validate_input(code)
        assert "代码行数超过限制" in str(exc_info.value)


class TestResultFormatting:
    """测试结果格式化"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_rfc_client = Mock()
        self.handler = ToolHandler(self.mock_rfc_client)
    
    def test_format_mcp_response_with_no_errors(self):
        """测试格式化无错误的结果"""
        result = CheckResult(
            success=True,
            has_errors=False,
            errors=[],
            message=""
        )
        
        response = self.handler.format_mcp_response(result)
        
        assert "content" in response
        assert len(response["content"]) == 1
        assert response["content"][0]["type"] == "text"
        assert "success" in response["content"][0]["text"]
    
    def test_format_mcp_response_with_errors(self):
        """测试格式化包含错误的结果"""
        result = CheckResult(
            success=True,
            has_errors=True,
            errors=[
                SyntaxError(line=5, type="E", message="未定义的变量"),
                SyntaxError(line=10, type="W", message="未使用的变量")
            ],
            message=""
        )
        
        response = self.handler.format_mcp_response(result)
        
        assert "content" in response
        assert "errors" in response["content"][0]["text"]
    
    def test_format_error_response(self):
        """测试格式化错误响应"""
        response = self.handler.format_error_response(
            "TEST_ERROR",
            "这是一个测试错误"
        )
        
        assert "error" in response
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "这是一个测试错误"


class TestCheckAbapSyntax:
    """测试 ABAP 语法检查功能"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_rfc_client = Mock()
        self.handler = ToolHandler(self.mock_rfc_client)
    
    def test_check_abap_syntax_success_no_errors(self):
        """测试成功检查无错误的代码"""
        code = "REPORT test.\nWRITE 'Hello'."
        
        # 模拟 RFC 响应
        self.mock_rfc_client.is_connected = True
        self.mock_rfc_client.call_function.return_value = {
            "EV_SUCCESS": "X",
            "EV_MESSAGE": "",
            "ET_ERRORS": []
        }
        
        result = self.handler.check_abap_syntax(code)
        
        assert result.success is True
        assert result.has_errors is False
        assert len(result.errors) == 0
        self.mock_rfc_client.call_function.assert_called_once()
    
    def test_check_abap_syntax_success_with_errors(self):
        """测试成功检查包含错误的代码"""
        code = "REPORT test.\nWRITE lv_undefined."
        
        # 模拟 RFC 响应
        self.mock_rfc_client.is_connected = True
        self.mock_rfc_client.call_function.return_value = {
            "EV_SUCCESS": "X",
            "EV_MESSAGE": "",
            "ET_ERRORS": [
                {"LINE": 2, "TYPE": "E", "MESSAGE": "未定义的变量 'LV_UNDEFINED'"}
            ]
        }
        
        result = self.handler.check_abap_syntax(code)
        
        assert result.success is True
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert result.errors[0].line == 2
    
    def test_check_abap_syntax_connects_if_not_connected(self):
        """测试未连接时自动建立连接"""
        code = "REPORT test."
        
        # 模拟未连接状态
        self.mock_rfc_client.is_connected = False
        self.mock_rfc_client.call_function.return_value = {
            "EV_SUCCESS": "X",
            "EV_MESSAGE": "",
            "ET_ERRORS": []
        }
        
        self.handler.check_abap_syntax(code)
        
        # 验证调用了 connect
        self.mock_rfc_client.connect.assert_called_once()
    
    def test_check_abap_syntax_with_invalid_input(self):
        """测试无效输入被拒绝"""
        with pytest.raises(InputValidationError):
            self.handler.check_abap_syntax("")


class TestHandleCheckSyntax:
    """测试完整的工具调用处理流程"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_rfc_client = Mock()
        self.handler = ToolHandler(self.mock_rfc_client)
    
    def test_handle_check_syntax_success(self):
        """测试成功处理工具调用"""
        arguments = {"code": "REPORT test.\nWRITE 'Hello'."}
        
        # 模拟 RFC 响应
        self.mock_rfc_client.is_connected = True
        self.mock_rfc_client.call_function.return_value = {
            "EV_SUCCESS": "X",
            "EV_MESSAGE": "",
            "ET_ERRORS": []
        }
        
        response = self.handler.handle_check_syntax(arguments)
        
        assert "content" in response
        assert "error" not in response
    
    def test_handle_check_syntax_with_missing_code(self):
        """测试缺少 code 参数返回错误"""
        arguments = {}
        
        response = self.handler.handle_check_syntax(arguments)
        
        assert "error" in response
        assert response["error"]["code"] == "INVALID_INPUT"
    
    def test_handle_check_syntax_with_empty_code(self):
        """测试空 code 参数返回错误"""
        arguments = {"code": ""}
        
        response = self.handler.handle_check_syntax(arguments)
        
        assert "error" in response
        assert response["error"]["code"] == "INVALID_INPUT"
    
    def test_handle_check_syntax_with_connection_error(self):
        """测试连接错误返回错误响应"""
        arguments = {"code": "REPORT test."}
        
        # 模拟连接错误
        self.mock_rfc_client.is_connected = False
        self.mock_rfc_client.connect.side_effect = RFCConnectionError("连接失败")
        
        response = self.handler.handle_check_syntax(arguments)
        
        assert "error" in response
        assert response["error"]["code"] == "CONNECTION_FAILED"
    
    def test_handle_check_syntax_with_rfc_call_error(self):
        """测试 RFC 调用错误返回错误响应"""
        arguments = {"code": "REPORT test."}
        
        # 模拟 RFC 调用错误
        self.mock_rfc_client.is_connected = True
        self.mock_rfc_client.call_function.side_effect = RFCCallError("函数不存在")
        
        response = self.handler.handle_check_syntax(arguments)
        
        assert "error" in response
        assert response["error"]["code"] == "RFC_CALL_FAILED"
