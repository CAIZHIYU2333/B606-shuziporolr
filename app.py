import os
import json
import asyncio
import base64
import threading
import time
import uuid
from typing import Dict, Any, Optional
from io import BytesIO

# 添加多进程支持
from multiprocessing import freeze_support

try:
    import requests  # type: ignore
except Exception:
    requests = None

# 导入dashscope相关模块
try:
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer as DashscopeSpeechSynthesizer  # type: ignore
    from dashscope.audio.tts_v2 import AudioFormat as DashscopeAudioFormat  # type: ignore
    from dashscope.audio.tts_v2 import ResultCallback as DashscopeResultCallback  # type: ignore
    HAS_DASHSCOPE = True
except Exception:
    # 为了满足Pyright类型检查，定义占位符
    class DashscopeSpeechSynthesizer:
        def __init__(self, **kwargs):
            pass
        def streaming_call(self, text):
            pass
        def streaming_complete(self):
            pass
    
    class DashscopeAudioFormat:
        PCM_24000HZ_MONO_16BIT = "PCM_24000HZ_MONO_16BIT"
    
    class DashscopeResultCallback:
        def on_open(self):
            pass
        def on_event(self, msg):
            pass
        def on_data(self, data):
            pass
        def on_complete(self):
            pass
        def on_error(self, msg):
            pass
        def on_close(self):
            pass
    
    HAS_DASHSCOPE = False
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify, Response, stream_template
from flask_socketio import SocketIO, emit, disconnect
# 类型注解用于Flask-SocketIO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from flask import Request
import cv2
import yaml
import io
import tempfile
import subprocess
import sys
import os
from pathlib import Path

# 导入历史记录管理器
from src.chat_history_manager import init_history_manager, get_history_manager

# 配置加载
def load_config():
    with open('config/glut2.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_permissions_config():
    with open('config/permissions.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()
permissions_config = load_permissions_config()

# 获取服务配置
service_config = config.get('default', {}).get('service', {})
HOST = service_config.get('host', '127.0.0.1')
PORT = service_config.get('port', 8282)

# 权限管理配置
PERMISSIONS = permissions_config.get('permissions', {}).get('roles', {
    'admin': ['read', 'write', 'delete', 'manage_users', 'access_knowledge_base'],
    'user': ['read', 'write'],
    'guest': ['read']
})

USER_ROLES = permissions_config.get('permissions', {}).get('users', {
    'admin': 'admin',
    'user1': 'user',
    'guest': 'guest'
})

# 获取系统提示词配置
SYSTEM_PROMPTS = permissions_config.get('system_prompts', [])

# 获取TTS选项配置
TTS_OPTIONS = permissions_config.get('tts_options', [])

# 获取LLM选项配置
LLM_OPTIONS = permissions_config.get('llm_options', [])

# 历史对话存储配置
HISTORY_STORAGE = permissions_config.get('history_storage', {})

KNOWLEDGE_BASE = {
    'topics': [
        {
            'id': 'kb001',
            'title': '数字人技术介绍',
            'content': '数字人技术是通过计算机图形学、人工智能等技术创建的虚拟人物...',
            'tags': ['数字人', 'AI', '虚拟形象']
        },
        {
            'id': 'kb002',
            'title': '语音识别技术',
            'content': '语音识别技术是将人类语音转换为文本的技术...',
            'tags': ['语音识别', 'ASR', '人工智能']
        },
        {
            'id': 'kb003',
            'title': '大语言模型',
            'content': '大语言模型是基于大量文本训练的深度学习模型...',
            'tags': ['LLM', '深度学习', '自然语言处理']
        }
    ]
}

# 初始化历史记录管理器
init_history_manager(HISTORY_STORAGE)

# 获取系统提示词配置
SYSTEM_PROMPTS = permissions_config.get('system_prompts', [])

# 获取TTS选项配置
TTS_OPTIONS = permissions_config.get('tts_options', [])

# 获取LLM选项配置
LLM_OPTIONS = permissions_config.get('llm_options', [])

# 历史对话存储配置
HISTORY_STORAGE = permissions_config.get('history_storage', {})

KNOWLEDGE_BASE = {
    'topics': [
        {
            'id': 'kb001',
            'title': '数字人技术介绍',
            'content': '数字人技术是通过计算机图形学、人工智能等技术创建的虚拟人物...',
            'tags': ['数字人', 'AI', '虚拟形象']
        },
        {
            'id': 'kb002',
            'title': '语音合成技术',
            'content': '语音合成技术是将文本转换为自然语音的技术...',
            'tags': ['TTS', '语音', '合成']
        }
    ]
}

# 全局变量，用于存储AvatarVideoStream实例
avatar_stream = None

def init_avatar_stream():
    """初始化AvatarVideoStream实例"""
    global avatar_stream
    if avatar_stream is None:
        try:
            avatar_stream = AvatarVideoStream()
            print("AvatarVideoStream初始化成功")
        except Exception as e:
            print(f"AvatarVideoStream初始化失败: {e}")
            import traceback
            traceback.print_exc()
            avatar_stream = None
    return avatar_stream

# 数字人视频流管理
class AvatarVideoStream:
    def __init__(self):
        self.avatar_config = config['default']['chat_engine']['handler_configs'].get('LiteAvatar', {})
        # 修复配置读取，确保正确获取avatar_name
        self.avatar_name = self.avatar_config.get('avatar_name', '20250408/sample_data')
        if not self.avatar_name or self.avatar_name in ['null', 'none', 'None']:
            self.avatar_name = '20250408/sample_data'
        # 确保 avatar_name 是字符串类型
        if not isinstance(self.avatar_name, str):
            self.avatar_name = str(self.avatar_name)
        self.fps = self.avatar_config.get('fps', 20)
        self.use_gpu = self.avatar_config.get('use_gpu', True)
        self.current_frame = None
        self.is_generating = False
        self.liteavatar_handler = None
        self._processor_started = False
        self.last_frame_time = time.time()
        self.frame_count = 0
        # 延迟初始化，避免多进程启动问题
        self.initialized = False
        self.init_error = None
        # 添加上下文管理
        self.context = None
        
    def initialize(self):
        """延迟初始化LiteAvatar处理器"""
        if self.initialized:
            return True
            
        try:
            self._init_liteavatar()
            self.initialized = True
            return True
        except Exception as e:
            self.init_error = str(e)
            print(f"数字人初始化失败: {e}")
            return False
    
    def _init_liteavatar(self):
        """初始化LiteAvatar处理器"""
        try:
            print(f"开始初始化LiteAvatar处理器，avatar_name: {self.avatar_name}")
            
            # 检查数字人资源文件
            if not self._check_avatar_resources():
                print(f"警告: 数字人资源文件不存在或下载失败，将使用模拟模式")
            
            # 添加项目根目录和src目录到sys.path
            project_root = os.getcwd()
            src_path = os.path.join(project_root, 'src')
            
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            print(f"当前Python路径: {sys.path}")
            print(f"尝试导入HandlerTts2Face...")
            
            # 尝试导入HandlerTts2Face
            from src.handlers.avatar.liteavatar.avatar_handler_liteavatar import HandlerTts2Face, Tts2FaceConfigModel
            print("HandlerTts2Face导入成功")
            
            # 正确初始化HandlerTts2Face
            self.liteavatar_handler = HandlerTts2Face()
            print("HandlerTts2Face实例化成功")
            
            # 创建配置模型
            config_model = Tts2FaceConfigModel(  # type: ignore
                avatar_name=self.avatar_name,
                fps=self.fps,
                use_gpu=self.use_gpu
            )
            print("配置模型创建成功")
            
            # 加载处理器
            # 创建一个空的ChatEngineConfigModel对象，如果不需要可以传None
            try:
                from chat_engine.data_models.chat_engine_config_data import ChatEngineConfigModel  # type: ignore
                engine_config = ChatEngineConfigModel()
            except ImportError:
                # 如果无法导入，创建一个简单的配置对象
                class SimpleEngineConfig:
                    pass
                engine_config = SimpleEngineConfig()
            self.liteavatar_handler.load(engine_config, config_model)  # type: ignore
            print("处理器加载成功")
            
            print(f"LiteAvatar处理器初始化成功: {self.avatar_name}")
        except ImportError as e:
            print(f"LiteAvatar模块导入失败: {e}")
            print("请确保src/handlers/avatar/liteavatar/avatar_handler_liteavatar.py文件存在")
            import traceback
            traceback.print_exc()
            self.liteavatar_handler = None
            raise e
        except Exception as e:
            print(f"LiteAvatar处理器初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self.liteavatar_handler = None
            # 不抛出异常，允许使用模拟模式
            print("将使用模拟模式运行数字人")
    
    def _check_avatar_resources(self):
        """检查数字人资源文件是否存在"""
        try:
            # 构建资源路径
            resource_dir = os.path.join(os.getcwd(), 'resource', 'avatar', 'liteavatar')
            # 确保 avatar_name 是字符串类型
            avatar_name = str(self.avatar_name)
            # 修复avatar_name路径处理 - 去除两端可能存在的引号和空格
            avatar_name = avatar_name.strip().strip('"').strip("'")
                
            avatar_dir = os.path.join(resource_dir, avatar_name)
            avatar_zip = os.path.join(resource_dir, f"{avatar_name}.zip")
            
            # 创建资源目录
            os.makedirs(resource_dir, exist_ok=True)
            
            # 检查资源是否存在
            if os.path.exists(avatar_dir):
                print(f"数字人资源目录已存在: {avatar_dir}")
                return True
            
            if os.path.exists(avatar_zip):
                print(f"数字人资源压缩包已存在: {avatar_zip}")
                # 尝试解压
                import zipfile
                try:
                    with zipfile.ZipFile(avatar_zip, 'r') as zip_ref:
                        zip_ref.extractall(os.path.dirname(avatar_zip))
                    print(f"数字人资源解压完成: {avatar_dir}")
                    return True
                except Exception as e:
                    print(f"数字人资源解压失败: {e}")
                    return False
            
            print(f"数字人资源文件不存在: {avatar_dir}")
            return False
        except Exception as e:
            print(f"检查数字人资源文件时出错: {e}")
            return False
    
    def _ensure_avatar_processor_started(self):
        """确保数字人处理器已启动"""
        try:
            if self.liteavatar_handler and not self._processor_started:
                # 发送启动事件
                from src.handlers.avatar.liteavatar.avatar_handler_liteavatar import Tts2FaceEvent
                self.liteavatar_handler.event_in_queue.put(Tts2FaceEvent.START)
                self._processor_started = True
                print("数字人处理器已启动")
                return True
            return self._processor_started if self.liteavatar_handler else False
        except Exception as e:
            print(f"启动数字人处理器失败: {e}")
            return False

    def generate_avatar_frame(self, text: str, speaking: bool = True):
        """生成数字人视频帧"""
        # 确保处理器已初始化
        if not self.initialized and not self.init_error:
            self.initialize()
        elif self.init_error:
            # 如果初始化失败，使用模拟帧
            frame = self._generate_fallback_frame()
            self.current_frame = frame
            return frame
        
        try:
            frame = None
            if self.liteavatar_handler and self._ensure_avatar_processor_started():
                # 尝试从视频队列获取真实帧
                try:
                    if hasattr(self.liteavatar_handler, 'video_out_queue') and not self.liteavatar_handler.video_out_queue.empty():
                        frame = self.liteavatar_handler.video_out_queue.get_nowait()
                        if frame is not None:
                            self.current_frame = frame
                            return frame
                except Exception as e:
                    print(f"从视频队列获取帧失败: {e}")
            
            # 如果没有获取到真实帧，则使用模拟帧
            if frame is None:
                frame = self._generate_simulation_frame(text, speaking)
                self.current_frame = frame
            return frame
        except Exception as e:
            print(f"生成数字人帧失败: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_frame()
    
    def _generate_simulation_frame(self, text: str, speaking: bool = True):
        """生成改进的模拟帧"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)  # 增大帧尺寸以适应更大的本地视频窗口
        
        # 更真实的背景
        for i in range(720):
            color = int(30 + (i / 720) * 40)
            frame[i, :] = [color, color + 10, color + 20]
        
        # 数字人头像区域
        center_x, center_y = 640, 360
        radius = 150
        
        # 头部轮廓（更真实）
        cv2.circle(frame, (center_x, center_y), radius, (180, 160, 140), -1)
        cv2.circle(frame, (center_x, center_y), radius, (120, 100, 80), 2)
        
        # 眼睛
        eye_radius = 20
        cv2.circle(frame, (center_x - 40, center_y - 30), eye_radius, (255, 255, 255), -1)
        cv2.circle(frame, (center_x + 40, center_y - 30), eye_radius, (255, 255, 255), -1)
        cv2.circle(frame, (center_x - 40, center_y - 30), int(eye_radius/2), (0, 0, 0), -1)
        cv2.circle(frame, (center_x + 40, center_y - 30), int(eye_radius/2), (0, 0, 0), -1)
        
        # 嘴巴（根据说话状态变化）
        # 嘴巴（根据说话状态变化）
        if speaking:
            # 张开的嘴巴
            mouth_width = 80
            mouth_height = 30 + (int(time.time() * 10) % 15)  # 动态变化
        else:
            # 闭合的嘴巴
            mouth_width = 50
            mouth_height = 8
            
        cv2.ellipse(frame, (center_x, center_y + 50), (mouth_width, mouth_height), 0, 0, 180, (0, 0, 0), -1)
        
        # 添加状态文本
        status_text = "数字人就绪" if not speaking else "正在说话..."
        cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        if text:
            # 显示部分文本（如果太长则截断）
            display_text = text[:50] + "..." if len(text) > 50 else text
            cv2.putText(frame, display_text, (20, 680), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return frame

    def _generate_fallback_frame(self):
        """生成降级帧"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(frame, "数字人连接失败", (400, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
        cv2.putText(frame, "正在显示模拟画面", (400, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
        return frame

    def get_frame_jpeg(self):
        """获取当前帧的JPEG编码"""
        # 确保处理器已初始化
        if not self.initialized and not self.init_error:
            self.initialize()
        elif self.init_error:
            # 如果初始化失败，生成错误帧
            if self.current_frame is None:
                self.current_frame = self._generate_fallback_frame()
        
        # 定期生成新帧以保持动画效果
        current_time = time.time()
        if current_time - self.last_frame_time > 1.0 / max(self.fps, 1):
            self.generate_avatar_frame("", speaking=False)
            self.last_frame_time = current_time
            self.frame_count += 1
        
        if self.current_frame is None:
            self.generate_avatar_frame("", speaking=False)
        
        try:
            # 尝试从LiteAvatar获取真实帧
            real_frame = None
            if self.liteavatar_handler and self._processor_started:
                try:
                    if hasattr(self.liteavatar_handler, 'video_out_queue') and not self.liteavatar_handler.video_out_queue.empty():
                        real_frame = self.liteavatar_handler.video_out_queue.get_nowait()
                        if real_frame is not None:
                            self.current_frame = real_frame
                except Exception as e:
                    print(f"从视频队列获取帧失败: {e}")
            
            if self.current_frame is not None:
                # 确保帧是正确的numpy数组类型
                frame = np.asarray(self.current_frame, dtype=np.uint8)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    return buffer.tobytes()
                else:
                    print(f"帧格式不正确: {frame.shape}")
                    return None
            else:
                print("当前帧为None，无法编码")
                return None
        except Exception as e:
            print(f"编码帧失败: {e}")
            return None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局状态管理
class ChatSession:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.is_active = False
        self.audio_buffer = []
        self.video_buffer = []
        self.chat_history = []
        self.current_avatar_state = "idle"
        self.llm_response = ""
        self.is_speaking = False

# 会话管理
sessions: Dict[str, ChatSession] = {}

# 权限检查装饰器
def require_permission(permission):
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            # 在实际应用中，这里会检查用户权限
            # 简化处理，假设所有用户都有基础权限
            return f(*args, **kwargs)
        wrapped_function.__name__ = f.__name__  # 修复Flask路由装饰器冲突问题
        return wrapped_function
    return decorator

# TTS结果回调类
class TTSResultCallback(DashscopeResultCallback):
    def __init__(self):
        super().__init__()
        self.audio_data = bytearray()
        
    def on_open(self):
        print("TTS连接已打开")
        self.audio_data.clear()
        
    def on_event(self, msg):
        print(f"TTS事件: {msg}")
        
    def on_data(self, data):
        # 收到音频数据
        self.audio_data.extend(data)
        
    def on_complete(self):
        print("TTS合成完成")
        
    def on_error(self, msg):
        print(f"TTS错误: {msg}")
        
    def on_close(self):
        print("TTS连接已关闭")

# 模拟AI处理函数
class AIProcessor:
    def __init__(self):
        self.config = config['default']['chat_engine']['handler_configs']
        # LLM配置（OpenAI兼容-百炼）
        self.llm_cfg = self.config.get('LLM_Bailian', {}) or {}
        self.model_name = self.llm_cfg.get('model_name')
        self.system_prompt = self.llm_cfg.get('system_prompt')
        self.api_url = self.llm_cfg.get('api_url')
        self.api_key = self.llm_cfg.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
        # TTS（CosyVoice）配置
        self.tts_cfg = self.config.get('CosyVoice', {}) or {}
        self.tts_voice = self.tts_cfg.get('voice', 'longjing')
        self.tts_model = self.tts_cfg.get('model_name', 'cosyvoice-v1')
        self.tts_sr = 24000
        if HAS_DASHSCOPE and self.api_key:
            import dashscope as ds
            ds.api_key = self.api_key
        
        # 流式TTS相关
        self.tts_queue = []
        self.tts_processing = False
        self.tts_thread = None
        self.tts_lock = threading.Lock()
        self.current_session_id = None
        
        # 当前使用的TTS模块
        self.current_tts_module = "cosyvoice"
        
        # 初始化dashscope TTS合成器
        self.dashscope_tts = None
        if HAS_DASHSCOPE and self.api_key and self.tts_voice:
            try:
                self.dashscope_tts = DashscopeSpeechSynthesizer(
                    model=self.tts_model,
                    voice=self.tts_voice,
                    format=DashscopeAudioFormat.PCM_24000HZ_MONO_16BIT,
                    callback=TTSResultCallback()
                )
                print("Dashscope TTS初始化成功")
            except Exception as e:
                print(f"Dashscope TTS初始化失败: {e}")
                self.dashscope_tts = None

        # 打印配置信息用于调试
        print(f"LLM配置信息:")
        print(f"  model_name: {self.model_name}")
        print(f"  api_url: {self.api_url}")
        print(f"  api_key存在: {bool(self.api_key)}")
        print(f"  system_prompt: {self.system_prompt[:50] if self.system_prompt else None}...")

    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt
        print(f"系统提示词已更新: {prompt[:50]}...")

    def set_llm_model(self, model_name: str, api_url: Optional[str] = None):
        """设置LLM模型"""
        self.model_name = model_name
        if api_url:
            self.api_url = api_url
        print(f"LLM模型已更新: {model_name}")

    def set_tts_module(self, module: str, config: dict):
        """设置TTS模块"""
        self.current_tts_module = module
        if module == "cosyvoice":
            # 配置阿里云CosyVoice
            self.tts_voice = config.get('voice', 'longjing')
            self.tts_model = config.get('model_name', 'cosyvoice-v1')
            api_key = config.get('api_key')
            self.tts_sr = config.get('sample_rate', 24000)
            
            if HAS_DASHSCOPE and api_key:
                import dashscope as ds
                ds.api_key = api_key
                try:
                    self.dashscope_tts = DashscopeSpeechSynthesizer(
                        model=self.tts_model,
                        voice=self.tts_voice,
                        format=DashscopeAudioFormat.PCM_24000HZ_MONO_16BIT,
                        callback=TTSResultCallback()
                    )
                    print("Dashscope TTS初始化成功")
                except Exception as e:
                    print(f"Dashscope TTS初始化失败: {e}")
                    self.dashscope_tts = None
        elif module == "edgetts":
            # Edge TTS配置（在处理函数中动态使用）
            self.tts_voice = config.get('voice', 'zh-CN-XiaoxiaoNeural')
            self.tts_sr = config.get('sample_rate', 24000)
            # Edge TTS将在使用时动态导入和调用
            self.dashscope_tts = None
            print("Edge TTS配置完成")

    def generate_response(self, text: str, history: Optional[list] = None) -> str:
        """生成AI回复"""
        if not self.api_url or not self.api_key or not self.model_name:
            # 模拟回复
            return f"我收到了您的消息：'{text}'。这是一条模拟回复，因为大模型服务未正确配置。"
            
        url = self.api_url.rstrip('/') + '/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if history:
            for h in history:
                role = 'user' if h.get('type') == 'user' else 'assistant'
                content = h.get('message')
                if content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": text})
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }
        try:
            if requests is None:
                import urllib.request
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, timeout=60) as r:
                    resp_text = r.read().decode('utf-8')
                data = json.loads(resp_text)
            else:
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
                resp.raise_for_status()
                data = resp.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content')
            if not content:
                content = (data.get('choices', [{}])[0].get('delta', {}) or {}).get('content', '')
            return content or "抱歉，我暂时没有生成到有效回答。"
        except Exception as e:
            print(f"LLM 请求失败: {e}")
            return "抱歉，当前大模型服务不可用，我会尽快恢复。"

    def generate_response_stream(self, text: str, history: Optional[list] = None):
        """流式生成：逐段yield文本"""
        print(f"[DEBUG] 开始流式生成回复，输入文本: {text}")  # 添加调试日志
        if not self.api_url or not self.api_key or not self.model_name:
            # 模拟流式回复
            fake_response = f"我收到了您的消息：'{text}'。这是一条模拟回复，因为大模型服务未正确配置。"
            # 按句子分段输出
            sentences = fake_response.split('。')
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    yield sentence + ("。" if i < len(sentences) - 1 else "")
                    time.sleep(0.5)  # 模拟延迟
            return
            
        url = self.api_url.rstrip('/') + '/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if history:
            for h in history:
                role = 'user' if h.get('type') == 'user' else 'assistant'
                content = h.get('message')
                if content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": text})
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": False}
        }
        try:
            if requests is None:
                import urllib.request
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, timeout=120) as r:
                    for raw in r:
                        try:
                            s = raw.decode('utf-8').strip()
                            if not s:
                                continue
                            if s.startswith('data:'):
                                s = s[5:].strip()
                            if s == '[DONE]':
                                break
                            obj = json.loads(s)
                            delta = obj.get('choices', [{}])[0].get('delta', {}).get('content')
                            if delta:
                                print(f"[DEBUG] 流式输出片段: {delta}")  # 添加调试日志
                                yield delta
                        except Exception:
                            continue
            else:
                with requests.post(url, headers=headers, data=json.dumps(payload), timeout=120, stream=True) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        s = line.strip()
                        if s.startswith('data:'):
                            s = s[5:].strip()
                        if s == '[DONE]':
                            break
                        try:
                            obj = json.loads(s)
                        except Exception:
                            continue
                        delta = obj.get('choices', [{}])[0].get('delta', {}).get('content')
                        if delta:
                            print(f"[DEBUG] 流式输出片段: {delta}")  # 添加调试日志
                            yield delta
        except Exception as e:
            print(f"LLM 流式失败: {e}")
            yield "抱歉，当前大模型服务不可用，我会尽快恢复。"
            return

    @staticmethod
    def _pcm16_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
        import struct
        byte_rate = sample_rate * channels * 2
        block_align = channels * 2
        subchunk2_size = len(pcm_bytes)
        chunk_size = 36 + subchunk2_size
        header = b''.join([
            b'RIFF',
            struct.pack('<I', chunk_size),
            b'WAVE',
            b'fmt ',
            struct.pack('<I', 16),
            struct.pack('<H', 1),
            struct.pack('<H', channels),
            struct.pack('<I', sample_rate),
            struct.pack('<I', byte_rate),
            struct.pack('<H', block_align),
            struct.pack('<H', 16),
            b'data',
            struct.pack('<I', subchunk2_size)
        ])
        return header + pcm_bytes

    def tts_synthesize_stream(self, text: str, session_id: str) -> Optional[bytes]:
        """流式TTS合成（将文本切片处理）"""
        if not text.strip():
            return None
            
        # 为流式输出添加延迟，避免文本片段过短导致的语音碎片化
        # 只有在文本足够长或者遇到句子结束标点时才进行TTS合成
        should_process = (
            len(text) >= 20 or  # 文本长度超过20个字符
            any(punct in text for punct in '。！？.') or  # 遇到句子结束标点
            text.endswith(('？', '！', '.', '?', '!'))  # 以问号或感叹号结尾
        )
        
        if should_process:
            if self.current_tts_module == "edgetts":
                # 使用Edge TTS
                audio_bytes: Optional[bytes] = None
                try:
                    import edge_tts
                    import asyncio
                    import numpy as np
                    
                    async def async_tts_call():
                        communicate = edge_tts.Communicate(text, self.tts_voice)
                        audio_data = b""
                        async for chunk in communicate.stream():
                            if chunk.get("type") == "audio" and "data" in chunk:
                                audio_data += chunk["data"]
                        return audio_data
                    
                    # 运行异步函数
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio_bytes = loop.run_until_complete(async_tts_call())
                    loop.close()
                    
                    # 发送音频数据到前端
                    if audio_bytes and len(audio_bytes) > 0:
                        # 使用numpy加载音频数据
                        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)  # 使用int16类型
                        
                        # 转换为正确的格式并发送
                        wav_bytes = self._pcm16_to_wav_bytes(audio_data.tobytes(), self.tts_sr)
                        
                        # 发送音频数据到前端
                        socketio.emit('tts_audio', {
                            'session_id': session_id,
                            'audio_wav_base64': base64.b64encode(wav_bytes).decode('utf-8'),
                            'sample_rate': self.tts_sr,
                            'format': 'wav',
                            'text': text
                        })
                        
                        # 返回音频数据供后续处理
                        return wav_bytes
                except Exception as e:
                    print(f"Edge TTS合成失败: {e}")
                    import traceback
                    traceback.print_exc()
                    audio_bytes = None
                finally:
                    # 确保资源被释放
                    if audio_bytes is not None:
                        try:
                            del audio_bytes
                        except:
                            pass
            elif self.dashscope_tts:
                # 使用阿里云CosyVoice TTS
                try:
                    # 清除之前的音频数据
                    callback = getattr(self.dashscope_tts, 'callback', None)  # type: ignore
                    if callback:
                        callback.audio_data.clear()
                    
                    # 开始流式合成
                    self.dashscope_tts.streaming_call(text)
                    
                    # 合成完成后触发事件
                    socketio.emit('tts_complete', {
                        'session_id': session_id,
                        'text': text
                    })
                    
                    # 收集音频数据
                    callback = getattr(self.dashscope_tts, 'callback', None)  # type: ignore
                    if callback:
                        audio_data = bytes(callback.audio_data)
                        
                        # 发送音频数据到前端
                        socketio.emit('tts_audio', {
                            'session_id': session_id,
                            'audio_wav_base64': base64.b64encode(audio_data).decode('utf-8'),
                            'sample_rate': self.tts_sr,
                            'format': 'pcm',
                            'text': text
                        })
                        
                        return audio_data
                        
                except Exception as e:
                    print(f"TTS合成失败: {e}")
                finally:
                    # 确保回调数据被清理
                    callback = getattr(self.dashscope_tts, 'callback', None)  # type: ignore
                    if callback:
                        try:
                            callback.audio_data.clear()
                        except:
                            pass
        return None
    
    def generate_avatar_animation(self, text: str) -> Dict[str, Any]:
        """生成虚拟形象动画数据"""
        # 确保avatar_stream已初始化
        global avatar_stream
        if avatar_stream is None:
            from app import init_avatar_stream
            avatar_stream = init_avatar_stream()
            
        # 触发数字人说话动画
        if avatar_stream:
            avatar_stream.generate_avatar_frame(text, speaking=True)
            
        # 生成动画数据
        return {
            "type": "animation",
            "expression": "speaking",
            "duration": max(1.5, len(text) * 0.08),  # 调整持续时间计算
            "lip_sync": self.generate_lip_sync(text),
            "text": text  # 添加文本内容
        }

    def stop_avatar_speaking(self):
        """停止数字人说话状态"""
        global avatar_stream
        if avatar_stream:
            avatar_stream.generate_avatar_frame("", speaking=False)
    
    def generate_lip_sync(self, text: str) -> list:
        """生成唇同步数据"""
        # 更精确的唇同步数据，基于文本长度和语速生成同步效果
        # 平均语速：每分钟150个字，即每个字约0.4秒
        duration = max(1.5, len(text) * 0.4)  # 最小持续时间1.5秒
        fps = 30  # 每秒帧数
        steps = int(duration * fps)  # 总帧数
        
        lip_data = []
        words = text.split()
        word_index = 0
        current_time = 0.0
        
        # 计算每个词的显示时间（基于平均语速）
        word_durations = [max(0.3, len(word) * 0.2) for word in words]  # 每个词至少0.3秒
        total_duration = sum(word_durations)
        
        # 如果总时长小于最小持续时间，调整每个词的时长
        if total_duration < duration and len(word_durations) > 0:
            scale_factor = duration / total_duration
            word_durations = [d * scale_factor for d in word_durations]
        
        for i in range(steps):
            time_in_seconds = i / fps
            
            # 找到当前时间对应的词
            while word_index < len(words) and current_time < time_in_seconds:
                current_time += word_durations[word_index]
                word_index += 1
            
            # 根据当前词的位置计算嘴巴开合程度
            if word_index < len(words):
                # 当前词的进度
                word_progress = (time_in_seconds - (current_time - word_durations[word_index-1])) / word_durations[word_index-1]
                
                # 基于音素分析的简单模型（这里只是模拟）
                # 实际应用中应该根据文本的音素进行更精确的计算
                base_open = 0.5 + 0.3 * abs(0.5 - word_progress) * 2
                
                # 根据位置调整开合程度（开始和结束时较小）
                position_factor = 1.0
                if word_progress < 0.2:  # 开始20%
                    position_factor = word_progress / 0.2
                elif word_progress > 0.8:  # 结束20%
                    position_factor = (1.0 - word_progress) / 0.2
                
                mouth_open = min(1.0, base_open * position_factor)
            else:
                mouth_open = 0.1  # 无词时嘴巴微张
            
            lip_data.append({"time": time_in_seconds, "mouth_open": mouth_open})
        
        return lip_data

ai_processor = AIProcessor()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html', config=config)

@app.route('/api/config', methods=['GET'])
@require_permission('read')
def get_config():
    """获取服务器配置"""
    try:
        return jsonify({
            "success": True,
            "config": {
                "host": HOST,
                "port": PORT,
                "system_prompts": SYSTEM_PROMPTS,
                "tts_options": TTS_OPTIONS,
                "llm_options": LLM_OPTIONS,
                "permissions": PERMISSIONS,
                "history_storage": HISTORY_STORAGE
            }
        })
    except Exception as e:
        print(f"获取配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/session/create', methods=['POST'])
@require_permission('write')
def create_session():
    """创建新的聊天会话"""
    try:
        # 检查请求内容类型
        if request.content_type and 'application/json' in request.content_type:
            request_data = request.get_json(silent=True) or {}
        else:
            request_data = {}
        
        session = ChatSession()
        sessions[session.session_id] = session
        
        response_data = {
            "success": True,
            "session_id": session.session_id,
            "status": "created"
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        print(f"创建会话失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/session/<session_id>/status', endpoint='get_session_status')
@require_permission('read')
def get_session_status(session_id):
    """获取会话状态"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session = sessions[session_id]
    return jsonify({
        "session_id": session_id,
        "is_active": session.is_active,
        "current_avatar_state": session.current_avatar_state,
        "is_speaking": session.is_speaking
    })

@app.route('/api/knowledge_base/search', methods=['POST'])
@require_permission('read')
def search_knowledge_base():
    """搜索知识库"""
    data = request.get_json()
    query = data.get('query', '')
    
    # 简单的关键词匹配搜索
    results = []
    for topic in KNOWLEDGE_BASE['topics']:
        # 检查标题、内容和标签是否包含查询词
        if (query.lower() in topic['title'].lower() or 
            query.lower() in topic['content'].lower() or
            any(query.lower() in tag.lower() for tag in topic['tags'])):
            results.append(topic)
    
    return jsonify({
        "success": True,
        "results": results
    })

@app.route('/api/knowledge_base/topics')
@require_permission('read')
def get_knowledge_topics():
    """获取所有知识库主题"""
    return jsonify({
        "success": True,
        "topics": KNOWLEDGE_BASE['topics']
    })

@app.route('/api/permissions')
@require_permission('manage_users')
def get_permissions():
    """获取权限列表"""
    return jsonify({
        "success": True,
        "permissions": PERMISSIONS
    })

@app.route('/api/llm/options', methods=['GET'])
@require_permission('read')
def get_llm_options():
    """获取LLM选项"""
    return jsonify({
        "success": True,
        "llm_options": LLM_OPTIONS
    })

@app.route('/api/llm/switch', methods=['POST'])
@require_permission('write')
def switch_llm():
    """切换LLM模型"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        api_url = data.get('api_url')
        
        # 更新AI处理器的LLM配置
        ai_processor.set_llm_model(model_name, api_url)
        
        return jsonify({
            "success": True,
            "message": f"已切换到模型: {model_name}"
        })
    except Exception as e:
        print(f"切换LLM失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tts/options', methods=['GET'])
@require_permission('read')
def get_tts_options():
    """获取TTS选项"""
    return jsonify({
        "success": True,
        "tts_options": TTS_OPTIONS
    })

@app.route('/api/tts/switch', methods=['POST'])
@require_permission('write')
def switch_tts():
    """切换TTS模块"""
    try:
        data = request.get_json()
        tts_name = data.get('tts_name')
        
        # 查找匹配的TTS配置
        selected_tts = None
        for tts_option in TTS_OPTIONS:
            if tts_option['name'] == tts_name:
                selected_tts = tts_option
                break
        
        if not selected_tts:
            return jsonify({"success": False, "error": "未找到指定的TTS选项"}), 400
        
        # 更新AI处理器的TTS配置
        module_name = "cosyvoice" if "cosyvoice" in selected_tts['module'] else "edgetts"
        ai_processor.set_tts_module(module_name, selected_tts['config'])
        
        return jsonify({
            "success": True,
            "message": f"已切换到 {tts_name}"
        })
    except Exception as e:
        print(f"切换TTS失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/system_prompts', methods=['GET'])
@require_permission('read')
def get_system_prompts():
    """获取系统提示词选项"""
    return jsonify({
        "success": True,
        "system_prompts": SYSTEM_PROMPTS
    })

@app.route('/api/system_prompt', methods=['POST'])
@require_permission('write')
def set_system_prompt():
    """设置系统提示词"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        prompt_name = data.get('prompt_name')
        
        if not prompt:
            return jsonify({"success": False, "error": "提示词不能为空"}), 400
        
        # 更新AI处理器的系统提示词
        ai_processor.set_system_prompt(prompt)
        
        return jsonify({
            "success": True,
            "message": f"系统提示词已更新为: {prompt_name or '自定义提示词'}"
        })
    except Exception as e:
        print(f"设置系统提示词失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history/sessions', methods=['GET'])
@require_permission('read')
def get_history_sessions():
    """获取历史会话列表"""
    try:
        sessions = get_history_manager().get_all_sessions()
        return jsonify({
            "success": True,
            "sessions": sessions
        })
    except Exception as e:
        print(f"获取历史会话列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history/session/<session_id>', methods=['GET'])
@require_permission('read')
def get_history_session(session_id):
    """获取特定会话的历史记录"""
    try:
        history = get_history_manager().get_session_history(session_id)
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        print(f"获取会话历史失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history/session/<session_id>', methods=['DELETE'])
@require_permission('delete')
def delete_history_session(session_id):
    """删除特定会话的历史记录"""
    try:
        success = get_history_manager().delete_session(session_id)
        if success:
            return jsonify({
                "success": True,
                "message": "会话历史已删除"
            })
        else:
            return jsonify({
                "success": False,
                "error": "会话不存在"
            }), 404
    except Exception as e:
        print(f"删除会话历史失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/avatar/video_feed')
def avatar_video_feed():
    """数字人视频流接口（MJPEG）"""
    try:
        # 确保avatar_stream已初始化
        global avatar_stream
        if avatar_stream is None:
            init_avatar_stream()
            
        def generate():
            while True:
                try:
                    if avatar_stream:
                        frame_bytes = avatar_stream.get_frame_jpeg()
                        if frame_bytes:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(1.0 / 30)  # 30 FPS
                except Exception as e:
                    print(f"视频流生成错误: {e}")
                    time.sleep(1)
                    
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"视频流接口错误: {e}")
        return "视频流不可用", 500

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    print('客户端已连接')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    print('客户端已断开连接')

@socketio.on('chat_message')
def handle_chat_message(data):
    """处理聊天消息"""
    session_id = data.get('session_id')
    message = data.get('message')
    
    # 如果没有session_id，则自动创建一个会话
    if not session_id:
        session = ChatSession()
        sessions[session.session_id] = session
        session_id = session.session_id
        print(f"自动创建会话: {session_id}")
    elif session_id not in sessions:
        # 如果session_id存在但无效，则创建新会话
        session = ChatSession()
        sessions[session.session_id] = session
        session_id = session.session_id
        print(f"会话不存在，创建新会话: {session_id}")
    
    if not message:
        emit('error', {'message': '缺少必要参数: 消息内容为空'})
        return
    
    session = sessions[session_id]
    
    # 添加用户消息到历史记录
    user_message_data = {
        'type': 'user',
        'message': message,
        'timestamp': time.time()
    }
    
    session.chat_history.append(user_message_data)
    
    # 保存到文件存储
    try:
        get_history_manager().add_message(session_id, user_message_data)
    except Exception as e:
        print(f"保存历史记录失败: {e}")
    
    print(f"收到用户消息: {message}")
    
    # 流式生成AI回复并实时处理TTS和数字人动画
    full_response = ""
    text_buffer = ""  # 用于积累文本以进行TTS合成
    
    # 使用流式生成
    for chunk in ai_processor.generate_response_stream(message, session.chat_history):
        if chunk:
            full_response += chunk
            text_buffer += chunk
            
            # 直接发送流式响应到客户端（不缓存）
            emit('chat_stream', {
                'session_id': session_id,
                'content': chunk
            })
            
            # 检查是否应该触发TTS合成和数字人动画
            should_process_tts = (
                len(text_buffer) >= 20 or  # 缓冲区足够大
                any(punct in chunk for punct in '。！？.') or  # 遇到句子结束标点
                chunk.endswith(('？', '！', '.', '?', '!'))  # 以问号或感叹号结尾
            )
            
            if should_process_tts and text_buffer.strip():
                # 触发TTS合成
                ai_processor.tts_synthesize_stream(text_buffer.strip(), session_id)
                
                # 触发数字人动画
                animation_data = ai_processor.generate_avatar_animation(text_buffer.strip())
                if animation_data and 'text' in animation_data:
                    emit('avatar_animation', animation_data)
                
                # 清空缓冲区
                text_buffer = ""
    
    # 处理剩余的文本
    if text_buffer.strip():
        # 触发TTS合成
        ai_processor.tts_synthesize_stream(text_buffer.strip(), session_id)
        
        # 触发数字人动画
        animation_data = ai_processor.generate_avatar_animation(text_buffer.strip())
        if animation_data and 'text' in animation_data:
            emit('avatar_animation', animation_data)
    
    # 发送流结束信号
    emit('chat_stream_end', {
        'session_id': session_id,
        'final_content': full_response
    })
    
    # 添加AI回复到历史记录
    ai_message_data = {
        'type': 'ai',
        'message': full_response,
        'timestamp': time.time()
    }
    
    session.chat_history.append(ai_message_data)
    
    # 保存到文件存储
    try:
        get_history_manager().add_message(session_id, ai_message_data)
    except Exception as e:
        print(f"保存历史记录失败: {e}")
    
    # 停止数字人说话状态
    ai_processor.stop_avatar_speaking()

if __name__ == '__main__':
    freeze_support()
    print(f"启动服务: http://{HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=False, allow_unsafe_werkzeug=True)