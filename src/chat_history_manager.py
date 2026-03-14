import json
import os
from typing import Dict, List, Any
from datetime import datetime
import threading


class ChatHistoryManager:
    """聊天历史记录管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.storage_path = config.get('storage_path', 'data/chat_history.json')
        self.max_sessions = config.get('max_sessions', 100)
        self.max_messages_per_session = config.get('max_messages_per_session', 100)
        self.enabled = config.get('enabled', True)
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else '.', exist_ok=True)
        
        # 线程锁确保并发安全
        self.lock = threading.Lock()
        
        # 加载历史记录
        self.history_data = self._load_history()
    
    def _load_history(self) -> Dict[str, Any]:
        """从文件加载历史记录"""
        if not self.enabled or not os.path.exists(self.storage_path):
            return {}
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return {}
    
    def _save_history(self):
        """保存历史记录到文件"""
        if not self.enabled:
            return
            
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_message(self, session_id: str, message_data: Dict[str, Any]):
        """添加消息到历史记录"""
        if not self.enabled:
            return
            
        with self.lock:
            # 初始化会话历史
            if session_id not in self.history_data:
                self.history_data[session_id] = {
                    'session_id': session_id,
                    'created_at': datetime.now().isoformat(),
                    'messages': []
                }
            
            # 添加消息
            self.history_data[session_id]['messages'].append(message_data)
            
            # 限制消息数量
            messages = self.history_data[session_id]['messages']
            if len(messages) > self.max_messages_per_session:
                # 保留最新的消息
                self.history_data[session_id]['messages'] = messages[-self.max_messages_per_session:]
            
            # 限制会话数量
            if len(self.history_data) > self.max_sessions:
                # 删除最旧的会话
                oldest_session_id = min(
                    self.history_data.keys(), 
                    key=lambda k: self.history_data[k]['created_at']
                )
                del self.history_data[oldest_session_id]
            
            # 保存到文件
            self._save_history()
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史记录"""
        if not self.enabled or session_id not in self.history_data:
            return []
        
        return self.history_data.get(session_id, {}).get('messages', [])
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话列表（不包含具体消息）"""
        if not self.enabled:
            return []
        
        sessions = []
        for session_id, session_data in self.history_data.items():
            sessions.append({
                'session_id': session_id,
                'created_at': session_data['created_at'],
                'message_count': len(session_data.get('messages', []))
            })
        
        # 按创建时间排序
        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话历史记录"""
        if not self.enabled or session_id not in self.history_data:
            return False
        
        with self.lock:
            del self.history_data[session_id]
            self._save_history()
            return True
    
    def clear_all_history(self):
        """清空所有历史记录"""
        if not self.enabled:
            return
            
        with self.lock:
            self.history_data.clear()
            self._save_history()


# 全局实例
history_manager = None


def init_history_manager(config: Dict[str, Any]):
    """初始化历史记录管理器"""
    global history_manager
    history_manager = ChatHistoryManager(config)


def get_history_manager() -> ChatHistoryManager:
    """获取历史记录管理器实例"""
    global history_manager
    if history_manager is None:
        raise RuntimeError("历史记录管理器未初始化")
    return history_manager