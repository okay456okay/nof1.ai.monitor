#!/usr/bin/env python3
"""
AI交易监控系统主程序
监控AI大模型的加密货币交易行为，并在有变化时发送企业微信通知
"""
import os
import sys
import logging
import argparse
from typing import Optional, List
from dotenv import load_dotenv

from trading_monitor import TradingMonitor


def setup_logging(log_level: str = "INFO"):
    """
    设置日志配置
    
    Args:
        log_level: 日志级别
    """
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 设置日志级别
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # 配置日志
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.FileHandler(f'{log_dir}/trading_monitor.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config() -> dict:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    # 尝试加载.env文件
    env_file = ".env"
    if not os.path.exists(env_file):
        env_file = "config.env.example"
        print(f"警告: 未找到 {env_file} 文件，使用示例配置文件")
        print("请复制 config.env.example 为 .env 并配置正确的参数")
    
    load_dotenv(env_file)
    
    # 获取配置
    config = {
        'wechat_webhook_url': os.getenv('WECHAT_WEBHOOK_URL'),
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
        'telegram_proxy': os.getenv('TELEGRAM_PROXY', '127.0.0.1:7890'),
        'monitored_models': os.getenv('MONITORED_MODELS', ''),
        'api_url': os.getenv('API_URL', 'https://nof1.ai/api'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'save_history_data': os.getenv('SAVE_HISTORY_DATA', 'False').lower() == 'true'
    }
    
    # 至少需要配置一个通知渠道（企业微信或Telegram）
    if not config['wechat_webhook_url'] and not (config['telegram_bot_token'] and config['telegram_chat_id']):
        print("警告: 未配置任何通知渠道，系统将只拉取与分析数据，不发送通知。")
    
    # 处理监控模型列表
    if config['monitored_models']:
        config['monitored_models'] = [model.strip() for model in config['monitored_models'].split(',') if model.strip()]
    else:
        config['monitored_models'] = None
    
    return config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI交易监控系统')
    parser.add_argument('--test', action='store_true', help='测试通知功能')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    parser.add_argument('--config', help='配置文件路径')
    
    args = parser.parse_args()
    
    try:
        # 设置日志
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        logger.info("AI交易监控系统启动")
        
        # 加载配置
        if args.config:
            os.environ['DOTENV_PATH'] = args.config
        
        config = load_config()
        
        logger.info(f"配置加载完成:")
        logger.info(f"  API地址: {config['api_url']}")
        logger.info("  通知渠道: {}{}".format(
            'WeChat ' if config['wechat_webhook_url'] else '',
            'Telegram' if (config['telegram_bot_token'] and config['telegram_chat_id']) else ''
        ))
        logger.info(f"  监控模型: {config['monitored_models'] or '全部模型'}")
        logger.info(f"  日志级别: {config['log_level']}")
        logger.info(f"  保存历史数据: {config['save_history_data']}")

        if config['api_url'].endswith('/account-totals'):
            config['api_url'] = config['api_url'].replace('/account-totals', '')
        
        # 创建监控器
        monitor = TradingMonitor(
            api_url=config['api_url'],
            wechat_webhook_url=config['wechat_webhook_url'],
            telegram_bot_token=config['telegram_bot_token'],
            telegram_chat_id=config['telegram_chat_id'],
            telegram_proxy=config['telegram_proxy'],
            monitored_models=config['monitored_models'],
            save_history_data=config['save_history_data']
        )
        
        # 测试模式
        if args.test:
            logger.info("运行测试模式")
            if monitor.test_notification():
                logger.info("测试通知发送成功")
                print("✅ 测试通知发送成功！请检查企业微信群是否收到消息。")
            else:
                logger.error("测试通知发送失败")
                print("❌ 测试通知发送失败！请检查配置是否正确。")
            return
        
        # 启动监控
        logger.info("开始启动监控系统...")
        print("🚀 AI交易监控系统已启动")
        print("📊 系统将每分钟检查一次持仓变化")
        print("📱 如有交易变化将发送企业微信通知")
        print("⏹️  按 Ctrl+C 停止监控")
        
        monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n👋 监控系统已停止")
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()