"""
MCP 服务器主程序

实现 ABAP 语法检查器 MCP 服务器，提供 check_abap_syntax 工具。
"""

import logging
import asyncio
from typing import Any, Optional
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.config import Config
from src.rfc_client import RFCClient, RFCConnectionError
from src.tool_handler import ToolHandler
from src.logger import setup_logging


logger = logging.getLogger(__name__)


class ABAPSyntaxCheckerServer:
    """
    ABAP 语法检查器 MCP 服务器
    
    提供 check_abap_syntax 工具，通过 RFC 连接到 SAP ERP 系统
    执行 ABAP REPORT 程序的语法检查。
    """
    
    def __init__(self, config: Config):
        """
        初始化 MCP 服务器
        
        Args:
            config: 服务器配置对象
        """
        self.config = config
        self.rfc_client: Optional[RFCClient] = None
        self.tool_handler: Optional[ToolHandler] = None
        self.server = Server("abap-syntax-checker")
        
        # 注册工具
        self._register_tools()
        
        logger.info("ABAP 语法检查器 MCP 服务器初始化完成")
    
    def _register_tools(self) -> None:
        """
        注册 MCP 工具
        
        注册 check_abap_syntax 工具并定义其输入模式。
        """
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """
            列出可用的工具
            
            Returns:
                list[Tool]: 工具列表
            """
            return [
                Tool(
                    name="check_abap_syntax",
                    description=(
                        "检查 ABAP REPORT 程序的语法错误。"
                        "该工具将 ABAP 代码发送到 SAP ERP 系统进行语法验证，"
                        "并返回详细的错误报告，包括错误行号、类型和描述。"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要检查的 ABAP REPORT 程序源代码"
                            }
                        },
                        "required": ["code"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """
            调用工具
            
            Args:
                name: 工具名称
                arguments: 工具参数
                
            Returns:
                list[TextContent]: 工具执行结果
                
            Raises:
                ValueError: 当工具名称未知时
            """
            if name != "check_abap_syntax":
                raise ValueError(f"未知工具: {name}")
            
            logger.info(f"收到工具调用请求: {name}")
            
            # 确保工具处理器已初始化
            if not self.tool_handler:
                error_msg = "工具处理器未初始化"
                logger.error(error_msg)
                return [TextContent(
                    type="text",
                    text=f'{{"error": {{"code": "NOT_INITIALIZED", "message": "{error_msg}"}}}}'
                )]
            
            # 处理工具调用
            result = self.tool_handler.handle_check_syntax(arguments)
            
            # 检查是否是错误响应
            if "error" in result:
                # 返回错误信息
                import json
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )]
            
            # 返回成功结果
            if "content" in result and len(result["content"]) > 0:
                return [TextContent(
                    type="text",
                    text=result["content"][0]["text"]
                )]
            
            # 默认返回
            return [TextContent(
                type="text",
                text='{"success": false, "message": "未知错误"}'
            )]
        
        logger.debug("MCP 工具注册完成")
    
    async def initialize(self) -> None:
        """
        初始化服务器组件
        
        建立 RFC 连接并初始化工具处理器。
        
        Raises:
            RFCConnectionError: 当 RFC 连接失败时
        """
        logger.info("正在初始化服务器组件")
        
        try:
            # 创建 RFC 客户端
            self.rfc_client = RFCClient(self.config.rfc)
            
            # 建立 RFC 连接
            logger.info("正在建立 RFC 连接")
            self.rfc_client.connect()
            logger.info("RFC 连接建立成功")
            
            # 创建工具处理器
            self.tool_handler = ToolHandler(self.rfc_client)
            logger.info("工具处理器初始化完成")
            
        except RFCConnectionError as e:
            logger.error(f"初始化失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"初始化过程中发生未预期错误: {str(e)}", exc_info=True)
            raise
    
    async def cleanup(self) -> None:
        """
        清理服务器资源
        
        关闭 RFC 连接并清理资源。
        """
        logger.info("正在清理服务器资源")
        
        try:
            if self.rfc_client:
                self.rfc_client.disconnect()
                logger.info("RFC 连接已关闭")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {str(e)}", exc_info=True)
    
    @asynccontextmanager
    async def lifespan(self):
        """
        服务器生命周期管理
        
        在服务器启动时初始化，在关闭时清理资源。
        """
        try:
            # 启动时初始化
            await self.initialize()
            logger.info("MCP 服务器启动成功")
            yield
        finally:
            # 关闭时清理
            await self.cleanup()
            logger.info("MCP 服务器已关闭")
    
    async def run(self) -> None:
        """
        运行 MCP 服务器
        
        启动服务器并通过 stdio 与客户端通信。
        """
        logger.info("启动 ABAP 语法检查器 MCP 服务器")
        
        async with self.lifespan():
            # 使用 stdio 传输运行服务器
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP 服务器正在运行，等待客户端连接")
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )


async def create_and_run_server(config: Config) -> None:
    """
    创建并运行 MCP 服务器
    
    Args:
        config: 服务器配置
    """
    # 配置日志系统
    setup_logging(
        log_level=config.log_level,
        log_file="abap_syntax_checker.log",
        enable_console=True,
        enable_color=True
    )
    
    logger.info("=" * 60)
    logger.info("ABAP 语法检查器 MCP 服务器")
    logger.info("=" * 60)
    
    # 创建并运行服务器
    server = ABAPSyntaxCheckerServer(config)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器")
    except Exception as e:
        logger.error(f"服务器运行时发生错误: {str(e)}", exc_info=True)
        raise


def main(config: Config) -> None:
    """
    主入口函数
    
    Args:
        config: 服务器配置
    """
    try:
        asyncio.run(create_and_run_server(config))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}", exc_info=True)
        raise
