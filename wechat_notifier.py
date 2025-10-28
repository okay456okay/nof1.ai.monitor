"""
企业微信机器人通知模块
负责发送交易变化通知到企业微信群
"""
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime


class WeChatNotifier:
    """企业微信通知器"""
    
    def __init__(self, webhook_url: str):
        """
        初始化企业微信通知器
        
        Args:
            webhook_url: 企业微信机器人webhook地址
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
    
    def _get_model_link(self, model_id: str) -> str:
        """
        获取模型持仓页面链接
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型持仓页面链接
        """
        return f"https://nof1.ai/models/{model_id}"
    
    def send_trade_notification(self, trades: List[Dict[str, Any]]) -> bool:
        """
        发送交易通知
        
        Args:
            trades: 交易变化列表
            
        Returns:
            发送成功返回True，失败返回False
        """
        if not trades:
            self.logger.info("无交易变化，跳过通知")
            return True
        
        try:
            # 生成通知内容
            content = self._generate_notification_content(trades)
            
            # 发送消息
            success = self._send_message(content)
            
            if success:
                self.logger.info(f"成功发送交易通知，包含 {len(trades)} 个交易变化")
            else:
                self.logger.error("发送交易通知失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"发送交易通知时发生错误: {e}")
            return False
    
    def _generate_notification_content(self, trades: List[Dict[str, Any]]) -> str:
        """
        生成通知内容
        
        Args:
            trades: 交易变化列表
            
        Returns:
            格式化的通知内容
        """
        # 标题
        content_lines = [
            "🚨 **AI交易监控提醒**",
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"📊 检测到 {len(trades)} 个交易变化:",
            "🔗 [全部持仓](http://alpha.insightpearl.com/)",
            ""
        ]
        
        # 按模型分组显示交易
        trades_by_model = {}
        for trade in trades:
            model_id = trade.get('model_id', 'unknown')
            if model_id not in trades_by_model:
                trades_by_model[model_id] = []
            trades_by_model[model_id].append(trade)
        
        # 生成每个模型的交易信息
        for model_id, model_trades in trades_by_model.items():
            model_link = self._get_model_link(model_id)
            content_lines.append(f"🤖 **{model_id}** [查看持仓]({model_link})")
            
            for trade in model_trades:
                trade_type = trade.get('type', 'unknown')
                message = trade.get('message', '')
                
                # 根据交易类型选择emoji
                if trade_type == 'position_opened':
                    emoji = "🟢"
                elif trade_type == 'position_closed':
                    emoji = "🔴"
                elif trade_type == 'position_changed':
                    action = trade.get('action', '')
                    if action == '买入':
                        emoji = "📈"
                    elif action == '卖出':
                        emoji = "📉"
                    else:
                        emoji = "⚙️"
                elif trade_type == 'model_added':
                    emoji = "🆕"
                elif trade_type == 'model_removed':
                    emoji = "❌"
                else:
                    emoji = "ℹ️"
                
                content_lines.append(f"  {emoji} {message}")
            
            content_lines.append("")  # 空行分隔
        
        return "\n".join(content_lines)
    
    def _send_message(self, content: str) -> bool:
        """
        发送消息到企业微信群
        
        Args:
            content: 消息内容
            
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            # 构建消息数据
            message_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            
            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=message_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # 检查响应
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                self.logger.info("企业微信消息发送成功")
                return True
            else:
                self.logger.error(f"企业微信消息发送失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"发送企业微信消息时网络错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发送企业微信消息时发生未知错误: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """
        发送测试消息
        
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            test_content = (
                "🧪 **AI交易监控系统测试**\n\n"
                "✅ 系统运行正常\n"
                f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "如果您收到此消息，说明通知功能配置正确！"
            )
            
            return self._send_message(test_content)
            
        except Exception as e:
            self.logger.error(f"发送测试消息时发生错误: {e}")
            return False
