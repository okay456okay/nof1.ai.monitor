"""
持仓数据获取模块
负责从API获取持仓数据并保存到本地文件
"""
import json
import logging
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class PositionDataFetcher:
    """持仓数据获取器"""
    
    def __init__(self, api_url: str):
        """
        初始化持仓数据获取器
        
        Args:
            api_url: API接口地址
        """
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)
        
    def fetch_positions(self) -> Optional[Dict[str, Any]]:
        """
        从API获取持仓数据
        
        Returns:
            持仓数据字典，如果获取失败返回None
        """
        try:
            self.logger.info(f"正在获取持仓数据: {self.api_url}")
            
            # 发送GET请求获取数据
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()  # 如果状态码不是200会抛出异常
            
            data = response.json()
            self.logger.info(f"成功获取持仓数据，包含 {len(data.get('positions', []))} 个模型")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取持仓数据失败: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"解析JSON数据失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取持仓数据时发生未知错误: {e}")
            return None
    
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
