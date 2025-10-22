"""
持仓变化检测和交易分析模块
负责比较两次持仓数据，识别交易行为并生成交易报告
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class TradeAnalyzer:
    """交易分析器"""
    
    def __init__(self):
        """初始化交易分析器"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_position_changes(self, last_data: Dict[str, Any], current_data: Dict[str, Any], 
                                monitored_models: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        分析持仓变化，识别交易行为
        
        Args:
            last_data: 上次持仓数据
            current_data: 当前持仓数据
            monitored_models: 要监控的模型列表，None表示监控所有模型
            
        Returns:
            交易变化列表
        """
        trades = []
        
        try:
            # 获取模型列表
            last_positions = last_data.get('positions', [])
            current_positions = current_data.get('positions', [])
            
            # 创建模型字典便于查找
            last_models = {pos['id']: pos for pos in last_positions}
            current_models = {pos['id']: pos for pos in current_positions}
            
            # 确定要检查的模型
            models_to_check = set(last_models.keys()) | set(current_models.keys())
            if monitored_models:
                models_to_check = models_to_check & set(monitored_models)
            
            self.logger.info(f"开始分析 {len(models_to_check)} 个模型的持仓变化")
            
            for model_id in models_to_check:
                last_model = last_models.get(model_id)
                current_model = current_models.get(model_id)
                
                # 分析该模型的持仓变化
                model_trades = self._analyze_model_changes(model_id, last_model, current_model)
                trades.extend(model_trades)
            
            self.logger.info(f"检测到 {len(trades)} 个交易变化")
            return trades
            
        except Exception as e:
            self.logger.error(f"分析持仓变化时发生错误: {e}")
            return []
    
    def _analyze_model_changes(self, model_id: str, last_model: Optional[Dict], 
                             current_model: Optional[Dict]) -> List[Dict[str, Any]]:
        """
        分析单个模型的持仓变化
        
        Args:
            model_id: 模型ID
            last_model: 上次模型持仓数据
            current_model: 当前模型持仓数据
            
        Returns:
            该模型的交易变化列表
        """
        trades = []
        
        try:
            # 处理模型新增或删除的情况
            if not last_model and current_model:
                # 新模型出现
                trades.append({
                    'type': 'model_added',
                    'model_id': model_id,
                    'message': f"新模型 {model_id} 开始交易",
                    'timestamp': datetime.now().isoformat()
                })
                return trades
            
            if last_model and not current_model:
                # 模型消失
                trades.append({
                    'type': 'model_removed',
                    'model_id': model_id,
                    'message': f"模型 {model_id} 停止交易",
                    'timestamp': datetime.now().isoformat()
                })
                return trades
            
            if not last_model or not current_model:
                return trades
            
            # 分析具体持仓变化
            last_positions = last_model.get('positions', {})
            current_positions = current_model.get('positions', {})
            
            # 检查所有交易对
            all_symbols = set(last_positions.keys()) | set(current_positions.keys())
            
            for symbol in all_symbols:
                last_pos = last_positions.get(symbol)
                current_pos = current_positions.get(symbol)
                
                symbol_trades = self._analyze_symbol_changes(model_id, symbol, last_pos, current_pos)
                trades.extend(symbol_trades)
            
            return trades
            
        except Exception as e:
            self.logger.error(f"分析模型 {model_id} 变化时发生错误: {e}")
            return []
    
    def _analyze_symbol_changes(self, model_id: str, symbol: str, 
                              last_pos: Optional[Dict], current_pos: Optional[Dict]) -> List[Dict[str, Any]]:
        """
        分析单个交易对的持仓变化
        
        Args:
            model_id: 模型ID
            symbol: 交易对符号
            last_pos: 上次持仓数据
            current_pos: 当前持仓数据
            
        Returns:
            该交易对的交易变化列表
        """
        trades = []
        
        try:
            # 处理持仓新增或删除的情况
            if not last_pos and current_pos:
                # 新开仓
                quantity = current_pos.get('quantity', 0)
                leverage = current_pos.get('leverage', 1)
                entry_price = current_pos.get('entry_price', 0)
                
                trades.append({
                    'type': 'position_opened',
                    'model_id': model_id,
                    'symbol': symbol,
                    'action': '买入' if quantity > 0 else '卖出',
                    'quantity': abs(quantity),
                    'leverage': leverage,
                    'entry_price': entry_price,
                    'message': f"{model_id} {symbol} 新开仓: {'买入' if quantity > 0 else '卖出'} {abs(quantity)} (杠杆: {leverage}x)",
                    'timestamp': datetime.now().isoformat()
                })
                return trades
            
            if last_pos and not current_pos:
                # 平仓
                trades.append({
                    'type': 'position_closed',
                    'model_id': model_id,
                    'symbol': symbol,
                    'message': f"{model_id} {symbol} 已平仓",
                    'timestamp': datetime.now().isoformat()
                })
                return trades
            
            if not last_pos or not current_pos:
                return trades
            
            # 比较持仓数量变化
            last_quantity = last_pos.get('quantity', 0)
            current_quantity = current_pos.get('quantity', 0)
            last_leverage = last_pos.get('leverage', 1)
            current_leverage = current_pos.get('leverage', 1)
            
            # 检查是否有变化
            if last_quantity != current_quantity or last_leverage != current_leverage:
                quantity_change = current_quantity - last_quantity
                
                if quantity_change > 0:
                    # 加仓
                    action = "买入"
                elif quantity_change < 0:
                    # 减仓
                    action = "卖出"
                else:
                    # 杠杆变化但数量不变
                    action = "调整杠杆"
                
                trades.append({
                    'type': 'position_changed',
                    'model_id': model_id,
                    'symbol': symbol,
                    'action': action,
                    'quantity_change': abs(quantity_change),
                    'last_quantity': last_quantity,
                    'current_quantity': current_quantity,
                    'last_leverage': last_leverage,
                    'current_leverage': current_leverage,
                    'current_price': current_pos.get('current_price', 0),
                    'message': self._format_trade_message(model_id, symbol, action, 
                                                        abs(quantity_change), current_leverage),
                    'timestamp': datetime.now().isoformat()
                })
            
            return trades
            
        except Exception as e:
            self.logger.error(f"分析 {model_id} {symbol} 变化时发生错误: {e}")
            return []
    
    def _format_trade_message(self, model_id: str, symbol: str, action: str, 
                            quantity_change: float, leverage: int) -> str:
        """
        格式化交易消息
        
        Args:
            model_id: 模型ID
            symbol: 交易对
            action: 交易动作
            quantity_change: 数量变化
            leverage: 杠杆倍数
            
        Returns:
            格式化的交易消息
        """
        if action == "调整杠杆":
            return f"{model_id} {symbol} 调整杠杆至 {leverage}x"
        else:
            return f"{model_id} {symbol} {action} {quantity_change} (杠杆: {leverage}x)"
    
    def generate_trade_summary(self, trades: List[Dict[str, Any]]) -> str:
        """
        生成交易摘要
        
        Args:
            trades: 交易列表
            
        Returns:
            交易摘要文本
        """
        if not trades:
            return "暂无交易变化"
        
        summary_lines = [f"检测到 {len(trades)} 个交易变化:"]
        
        for trade in trades:
            summary_lines.append(f"• {trade['message']}")
        
        return "\n".join(summary_lines)
