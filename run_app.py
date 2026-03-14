#!/usr/bin/env python3
"""
AI虚拟形象聊天系统启动脚本
"""

import os
import sys
import subprocess

def check_dependencies():
    """检查依赖项是否已安装"""
    required_packages = [
        'flask',
        'flask_socketio', 
        'numpy',
        'PIL',
        'cv2',
        'yaml'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少以下依赖项:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖项:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("AI虚拟形象聊天系统")
    print("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置文件
    if not os.path.exists('config/glut2.yaml'):
        print("错误: 找不到配置文件 config/glut2.yaml")
        print("请确保配置文件存在")
        sys.exit(1)
    
    # 检查模板和静态文件
    if not os.path.exists('templates/index.html'):
        print("错误: 找不到模板文件 templates/index.html")
        sys.exit(1)
    
    if not os.path.exists('static/css/style.css'):
        print("错误: 找不到样式文件 static/css/style.css")
        sys.exit(1)
    
    if not os.path.exists('static/js/app.js'):
        print("错误: 找不到JavaScript文件 static/js/app.js")
        sys.exit(1)
    
    print("✓ 所有文件检查通过")
    print("✓ 依赖项检查通过")
    print("\n正在启动应用...")
    
    try:
        # 启动Flask应用
        from app import app, socketio, config
        
        host = config['default']['service']['host']
        port = config['default']['service']['port']
        
        print(f"服务地址: http://{host}:{port}")
        print(f"WebSocket地址: ws://{host}:{port}")
        print("\n按 Ctrl+C 停止服务")
        
        socketio.run(app, host=host, port=port, debug=True)
        
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 