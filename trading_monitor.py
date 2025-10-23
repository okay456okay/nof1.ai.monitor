"""
定时任务调度模块
负责管理定时获取持仓数据和监控任务
"""
import logging
import schedule
import time
from typing import Optional, List
from datetime import datetime

from position_fetcher import PositionDataFetcher
from trade_analyzer import TradeAnalyzer
from wechat_notifier import WeChatNotifier


class TradingMonitor:
    """交易监控器"""
    
    def __init__(self, api_url: str, webhook_url: str, monitored_models: Optional[List[str]] = None):
        """
        初始化交易监控器
        
        Args:
            api_url: API接口地址
            webhook_url: 企业微信机器人webhook地址
            monitored_models: 要监控的模型列表，None表示监控所有模型
        """
        self.api_url = api_url
        self.webhook_url = webhook_url
        self.monitored_models = monitored_models
        
        # 初始化各个组件
        self.position_fetcher = PositionDataFetcher(api_url)
        self.trade_analyzer = TradeAnalyzer()
        self.notifier = WeChatNotifier(webhook_url)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 设置定时任务
        self._setup_schedule()
    
    def _setup_schedule(self):
        """设置定时任务"""
        # 每分钟执行一次监控任务
        schedule.every().minute.do(self._monitor_task)
        
        self.logger.info("定时任务已设置：每分钟执行一次监控")
    
    def _monitor_task(self):
        """
        监控任务主函数
        每分钟执行一次，获取持仓数据并分析变化
        """
        try:
            self.logger.info("开始执行监控任务")
            
            # 1. 获取当前持仓数据
            current_data = self.position_fetcher.fetch_positions()
            if not current_data:
                self.logger.info("获取持仓数据失败或为空，跳过本次监控")
                return
            
            # 2. 保存当前数据
            if not self.position_fetcher.save_positions(current_data, "current.json"):
                self.logger.error("保存当前持仓数据失败")
                return
            
            # 3. 检查是否存在上次数据
            last_data = self.position_fetcher.load_positions("last.json")
            if not last_data:
                self.logger.info("首次运行，无历史数据可比较")
                # 将当前数据重命名为历史数据，为下次比较做准备
                self.position_fetcher.rename_current_to_last()
                self.logger.info("监控任务执行完成（首次运行）")
                return
            
            # 4. 分析持仓变化
            trades = self.trade_analyzer.analyze_position_changes(
                last_data, current_data, self.monitored_models
            )
            
            # 5. 如果有交易变化，发送通知
            if trades:
                self.logger.info(f"检测到 {len(trades)} 个交易变化，准备发送通知")
                
                # 发送通知
                if self.notifier.send_trade_notification(trades):
                    self.logger.info("交易通知发送成功")
                else:
                    self.logger.error("交易通知发送失败")
                
                # 打印交易摘要到日志
                summary = self.trade_analyzer.generate_trade_summary(trades)
                self.logger.info(f"交易摘要:\n{summary}")
            else:
                self.logger.info("无交易变化")
            
            # 6. 将当前数据重命名为历史数据（只有在成功处理数据后才重命名）
            self.position_fetcher.rename_current_to_last()
            
            self.logger.info("监控任务执行完成")
            
        except Exception as e:
            self.logger.error(f"执行监控任务时发生错误: {e}")
    
    def start_monitoring(self):
        """
        开始监控
        启动定时任务并持续运行
        """
        self.logger.info("开始启动交易监控系统")
        
        # 发送启动通知
        try:
            startup_message = (
                "🚀 **AI交易监控系统启动**\n\n"
                f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔗 API地址: {self.api_url}\n"
                f"👀 监控模型: {', '.join(self.monitored_models) if self.monitored_models else '全部模型'}\n\n"
                "✅ 系统已开始监控，将每分钟检查一次持仓变化"
            )
            
            # 构建消息数据
            message_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": startup_message
                }
            }
            
            import requests
            response = requests.post(
                self.webhook_url,
                json=message_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("启动通知发送成功")
            else:
                self.logger.warning("启动通知发送失败")
                
        except Exception as e:
            self.logger.warning(f"发送启动通知时发生错误: {e}")
        
        # 开始定时任务循环
        self.logger.info("定时任务循环已启动")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，正在关闭监控系统...")
            self._send_shutdown_notification()
        except Exception as e:
            self.logger.error(f"监控系统运行时发生错误: {e}")
            self._send_error_notification(str(e))
    
    def _send_shutdown_notification(self):
        """发送关闭通知"""
        try:
            shutdown_message = (
                "🛑 **AI交易监控系统关闭**\n\n"
                f"⏰ 关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "系统已安全关闭"
            )
            
            message_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": shutdown_message
                }
            }
            
            import requests
            requests.post(
                self.webhook_url,
                json=message_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            self.logger.info("关闭通知发送成功")
            
        except Exception as e:
            self.logger.warning(f"发送关闭通知时发生错误: {e}")
    
    def _send_error_notification(self, error_message: str):
        """发送错误通知"""
        try:
            error_notification = (
                "❌ **AI交易监控系统错误**\n\n"
                f"⏰ 错误时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🚨 错误信息: {error_message}\n\n"
                "请检查系统状态"
            )
            
            message_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": error_notification
                }
            }
            
            import requests
            requests.post(
                self.webhook_url,
                json=message_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            self.logger.info("错误通知发送成功")
            
        except Exception as e:
            self.logger.error(f"发送错误通知时发生错误: {e}")
    
    def test_notification(self):
        """测试通知功能"""
        self.logger.info("测试通知功能")
        return self.notifier.send_test_message()
