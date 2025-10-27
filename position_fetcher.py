"""
持仓数据获取模块
负责从API获取持仓数据并保存到本地文件
"""
import json
import logging
import os
from venv import logger

import requests
from typing import Dict, Any, Optional
from datetime import datetime


class PositionDataFetcher:
    """持仓数据获取器"""
    
    def __init__(self, api_url: str, save_history_data: bool = False):
        """
        初始化持仓数据获取器
        
        Args:
            api_url: API接口地址
            save_history_data: 是否保存历史数据到data目录，默认为False
        """
        self.api_url = api_url
        self.save_history_data = save_history_data
        self.logger = logging.getLogger(__name__)
    
    def _calculate_last_hourly_marker(self) -> int:
        """
        计算lastHourlyMarker参数
        基于当前时间与2025年10月18日6:00:00的时间差计算小时数
        
        Returns:
            小时数标记
        """
        try:
            # 基准时间：2025年10月18日6:00:00
            base_time = datetime(2025, 10, 18, 6, 0, 0, 0)
            current_time = datetime.now()
            
            # 计算时间差（秒）
            time_diff_seconds = current_time.timestamp() - base_time.timestamp()
            
            # 转换为小时数
            hourly_marker = int(time_diff_seconds / 3600)
            
            self.logger.debug(f"计算lastHourlyMarker: {hourly_marker} (基准时间: {base_time}, 当前时间: {current_time})")
            return hourly_marker
            
        except Exception as e:
            self.logger.error(f"计算lastHourlyMarker失败: {e}")
            # 返回默认值
            return 129
    
    def save_data_to_file(self, data: Dict[str, Any], data_dir: str = "data") -> str:
        """
        保存数据到文件，文件名使用时间戳
        
        Args:
            data: 要保存的数据
            data_dir: 数据目录
            
        Returns:
            保存的文件路径
        """
        try:
            # 创建数据目录
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                self.logger.info(f"创建数据目录: {data_dir}")
            
            # 生成时间戳文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{data_dir}/positions_{timestamp}.json"
            
            # 保存数据
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据已保存到文件: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"保存数据到文件失败: {e}")
            return ""
        
    def fetch_positions(self) -> Optional[Dict[str, Any]]:
        """
        从API获取持仓数据
        
        Returns:
            持仓数据字典，如果获取失败返回None
        """
        try:
            # 计算lastHourlyMarker参数
            hourly_marker = self._calculate_last_hourly_marker()
            
            # 构建新的API URL
            api_url = f"https://nof1.ai/api/account-totals?lastHourlyMarker={hourly_marker}"
            
            self.logger.info(f"正在获取持仓数据: {api_url}")
            
            # 发送GET请求获取数据
            response = requests.get(api_url, timeout=60)
            response.raise_for_status()  # 如果状态码不是200会抛出异常
            data = response.json()

            if len(data.get('accountTotals', [])) == 0:
                self.logger.info(f"小时数据未获取到，获取全量数据")
                response = requests.get('https://nof1.ai/api/account-totals', timeout=60)
                data = response.json()
                try:
                    data['accountTotals'] = data.get('accountTotals', [])[-7:]
                except Exception as e:
                    self.logger.error(f"解析全量数据有问题： {e}，全量数据获取条数: {len(data['accountTotals'])}")

            # 转换数据格式以保持向后兼容
            converted_data = self._convert_to_legacy_format(data)
            
            # 如果转换后的数据为空，返回None
            if converted_data is None:
                self.logger.info("API返回空数据，跳过本次检测")
                return None
            
            self.logger.info(f"成功获取持仓数据，包含 {len(converted_data.get('positions', []))} 个模型")
            
            # 根据配置决定是否保存到data目录
            if self.save_history_data:
                self.logger.info("启用历史数据保存，保存数据到data目录")
                self.save_data_to_file(data, "data")
            else:
                self.logger.debug("未启用历史数据保存，跳过数据文件保存")
            
            return converted_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取持仓数据失败: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"解析JSON数据失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取持仓数据时发生未知错误: {e}")
            return None
    
    def _convert_to_legacy_format(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将新的API数据格式转换为旧的格式以保持向后兼容
        
        Args:
            new_data: 新API返回的数据
            
        Returns:
            转换后的数据格式，如果数据为空则返回None
        """
        try:
            account_totals = new_data.get('accountTotals', [])
            
            # 检查是否为空数据
            if not account_totals:
                self.logger.warning("API返回空数据，跳过本次检测")
                return None
            
            converted_positions = []
            
            for account in account_totals:
                model_id = account.get('model_id', 'unknown')
                positions = account.get('positions', {})
                
                # 转换每个模型的持仓数据
                converted_model = {
                    'id': model_id,
                    'timestamp': account.get('timestamp', 0),
                    'realized_pnl': account.get('realized_pnl', 0),
                    'positions': {}
                }
                
                # 转换每个交易对的持仓信息
                for symbol, position_data in positions.items():
                    converted_model['positions'][symbol] = {
                        'symbol': symbol,
                        'quantity': position_data.get('quantity', 0),
                        'leverage': position_data.get('leverage', 1),
                        'entry_price': position_data.get('entry_price', 0),
                        'current_price': position_data.get('current_price', 0),
                        'margin': position_data.get('margin', 0),
                        'unrealized_pnl': position_data.get('unrealized_pnl', 0),
                        'closed_pnl': position_data.get('closed_pnl', 0),
                        'risk_usd': position_data.get('risk_usd', 0),
                        'confidence': position_data.get('confidence', 0),
                        'entry_time': position_data.get('entry_time', 0),
                        'liquidation_price': position_data.get('liquidation_price', 0),
                        'commission': position_data.get('commission', 0),
                        'slippage': position_data.get('slippage', 0),
                        'oid': position_data.get('oid', 0),
                        'entry_oid': position_data.get('entry_oid', 0),
                        'tp_oid': position_data.get('tp_oid', -1),
                        'sl_oid': position_data.get('sl_oid', -1),
                        'wait_for_fill': position_data.get('wait_for_fill', False),
                        'index_col': position_data.get('index_col'),
                        'exit_plan': position_data.get('exit_plan', {})
                    }
                
                converted_positions.append(converted_model)
            
            # 返回兼容的格式
            return {
                'positions': converted_positions,
                'fetch_time': datetime.now().isoformat(),
                'timestamp': datetime.now().timestamp(),
                'raw_data': new_data  # 保留原始数据以备后用
            }
            
        except Exception as e:
            self.logger.error(f"转换数据格式失败: {e}")
            # 返回空数据
            return {
                'positions': [],
                'fetch_time': datetime.now().isoformat(),
                'timestamp': datetime.now().timestamp(),
                'raw_data': new_data
            }
    
    def save_positions(self, data: Dict[str, Any], filename: str = "current.json") -> bool:
        """
        保存持仓数据到文件
        
        Args:
            data: 持仓数据
            filename: 文件名
            
        Returns:
            保存成功返回True，失败返回False
        """
        try:
            # 添加保存时间戳
            data_with_timestamp = {
                **data,
                "fetch_time": datetime.now().isoformat(),
                "timestamp": datetime.now().timestamp()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_with_timestamp, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"持仓数据已保存到 {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存持仓数据失败: {e}")
            return False
    
    def load_positions(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载持仓数据
        
        Args:
            filename: 文件名
            
        Returns:
            持仓数据字典，如果文件不存在或加载失败返回None
        """
        try:
            if not os.path.exists(filename):
                self.logger.warning(f"文件 {filename} 不存在")
                return None
                
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"成功加载持仓数据: {filename}")
            return data
            
        except Exception as e:
            self.logger.error(f"加载持仓数据失败: {e}")
            return None
    
    def rename_current_to_last(self) -> bool:
        """
        将current.json重命名为last.json
        
        Returns:
            重命名成功返回True，失败返回False
        """
        try:
            if os.path.exists("current.json"):
                if os.path.exists("last.json"):
                    os.remove("last.json")  # 删除旧的last.json
                
                os.rename("current.json", "last.json")
                self.logger.info("current.json 已重命名为 last.json")
                return True
            else:
                self.logger.warning("current.json 文件不存在，无法重命名")
                return False
                
        except Exception as e:
            self.logger.error(f"重命名文件失败: {e}")
            return False
