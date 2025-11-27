"""
主入口文件

提供命令行接口启动 ABAP 语法检查器 MCP 服务器。
"""

import sys
import argparse
import logging
from pathlib import Path

from src.config import Config
from src.server import main as server_main


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="ABAP 语法检查器 MCP 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用环境变量配置
  python -m src.main
  
  # 使用配置文件
  python -m src.main --config config.json
  
  # 指定日志级别
  python -m src.main --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="配置文件路径（JSON 格式）"
    )
    
    parser.add_argument(
        "--log-level",
        "-l",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别（覆盖配置文件中的设置）"
    )
    
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> Config:
    """
    加载配置
    
    Args:
        args: 命令行参数
        
    Returns:
        Config: 配置对象
        
    Raises:
        SystemExit: 当配置加载失败时
    """
    try:
        # 从配置文件或环境变量加载
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"错误: 配置文件不存在: {args.config}", file=sys.stderr)
                sys.exit(1)
            
            print(f"从配置文件加载配置: {args.config}")
            config = Config.from_file(args.config)
        else:
            print("从环境变量加载配置")
            config = Config.from_env()
        
        # 覆盖日志级别（如果指定）
        if args.log_level:
            config.log_level = args.log_level
        
        return config
        
    except ValueError as e:
        print(f"错误: 配置无效: {str(e)}", file=sys.stderr)
        print("\n请确保以下配置参数已设置:", file=sys.stderr)
        print("  - SAP_HOST (或 config.json 中的 rfc.host)", file=sys.stderr)
        print("  - SAP_SYSNR (或 config.json 中的 rfc.sysnr)", file=sys.stderr)
        print("  - SAP_CLIENT (或 config.json 中的 rfc.client)", file=sys.stderr)
        print("  - SAP_USER (或 config.json 中的 rfc.user)", file=sys.stderr)
        print("  - SAP_PASSWORD (或 config.json 中的 rfc.password)", file=sys.stderr)
        sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"错误: 加载配置时发生未预期错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 加载配置
    config = load_config(args)
    
    # 启动服务器
    try:
        server_main(config)
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)
    except Exception as e:
        logging.error(f"服务器运行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
