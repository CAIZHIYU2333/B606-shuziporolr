#!/usr/bin/env python3
"""
AI虚拟形象聊天系统测试脚本
"""

import os
import sys
import json
import requests
from urllib.parse import urljoin

def test_file_structure():
    """测试文件结构"""
    print("🔍 检查文件结构...")
    
    required_files = [
        'app.py',
        'config/glut2.yaml',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少以下文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

def test_imports():
    """测试Python导入"""
    print("\n🔍 检查Python导入...")
    
    try:
        from app import app, socketio, config
        print("✅ Flask应用导入成功")
        print(f"✅ 配置加载成功，端口: {config['default']['service']['port']}")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n🔍 检查配置文件...")
    
    try:
        from app import config
        
        required_configs = [
            'default.service.host',
            'default.service.port',
            'default.chat_engine.handler_configs'
        ]
        
        for config_path in required_configs:
            keys = config_path.split('.')
            value = config
            for key in keys:
                value = value[key]
            print(f"✅ {config_path}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def test_html_template():
    """测试HTML模板"""
    print("\n🔍 检查HTML模板...")
    
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        required_elements = [
            ('app-container', 'class="app-container"'),
            ('localVideo', 'id="localVideo"'),
            ('avatarDisplay', 'id="avatarDisplay"'),
            ('chatMessages', 'id="chatMessages"'),
            ('messageInput', 'id="messageInput"'),
            ('avatarToggle', 'id="avatarToggle"')
        ]
        
        missing_elements = []
        for element_name, element_attr in required_elements:
            if element_attr not in html_content:
                missing_elements.append(element_name)
        
        if missing_elements:
            print(f"❌ HTML模板缺少元素: {missing_elements}")
            return False
        else:
            print("✅ HTML模板检查通过")
            return True
    except Exception as e:
        print(f"❌ HTML模板检查失败: {e}")
        return False

def test_css_styles():
    """测试CSS样式"""
    print("\n🔍 检查CSS样式...")
    
    try:
        with open('static/css/style.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        required_classes = [
            '.app-container',
            '.header',
            '.video-container',
            '.chat-section',
            '.btn',
            '.modal'
        ]
        
        missing_classes = []
        for class_name in required_classes:
            if class_name not in css_content:
                missing_classes.append(class_name)
        
        if missing_classes:
            print(f"❌ CSS缺少样式类: {missing_classes}")
            return False
        else:
            print("✅ CSS样式检查通过")
            return True
    except Exception as e:
        print(f"❌ CSS样式检查失败: {e}")
        return False

def test_javascript():
    """测试JavaScript代码"""
    print("\n🔍 检查JavaScript代码...")
    
    try:
        with open('static/js/app.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        required_functions = [
            'class AvatarChatApp',
            'initializeSocket',
            'startLocalStream',
            'sendChatMessage',
            'showNotification'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if func_name not in js_content:
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"❌ JavaScript缺少函数: {missing_functions}")
            return False
        else:
            print("✅ JavaScript代码检查通过")
            return True
    except Exception as e:
        print(f"❌ JavaScript检查失败: {e}")
        return False

def test_flask_app():
    """测试Flask应用"""
    print("\n🔍 检查Flask应用...")
    
    try:
        from app import app
        
        # 检查路由
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/api/session/create', '/api/config', '/api/health']
        
        missing_routes = []
        for route in required_routes:
            if route not in routes:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"❌ 缺少路由: {missing_routes}")
            return False
        else:
            print("✅ Flask路由检查通过")
            return True
    except Exception as e:
        print(f"❌ Flask应用检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("AI虚拟形象聊天系统 - 功能测试")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_imports,
        test_config,
        test_html_template,
        test_css_styles,
        test_javascript,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用可以正常运行。")
        print("\n启动应用:")
        print("python run_app.py")
        print("\n或者:")
        print("python app.py")
        return True
    else:
        print("❌ 部分测试失败，请检查上述问题。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 