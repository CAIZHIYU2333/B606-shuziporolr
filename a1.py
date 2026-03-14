import os  # 导入os模块，用于操作系统相关功能，如路径、环境变量等
import subprocess  # 导入subprocess模块，用于创建新进程并运行外部命令
import sys  # 导入sys模块，主要用于与Python解释器交互（本脚本未直接用到）

def main():
    """主函数：设置环境变量并运行主程序"""

    # 1. 获取当前工作目录
    current_dir = os.getcwd()  
    # 作用：获取当前脚本运行的目录，后续拼接路径时作为根目录使用
    # 控制：所有依赖本地路径的环境变量都基于此目录

    # 2. 设置环境变量字典
    env_vars = {
        # Python解释器路径，指定项目自带的Python环境
        'PYTHON': os.path.join(current_dir, '.glut', 'python.exe'),
        # CUDA库路径，供PyTorch等深度学习库调用GPU加速
        'CU_PATH': os.path.join(current_dir, '.glut', 'Lib', 'site-packages', 'torch', 'lib'),
        # Python脚本路径，包含pip等工具
        'SC_PATH': os.path.join(current_dir, '.glut', 'Scripts'),
        # FFMPEG工具路径，音视频处理依赖
        'FFMPEG_PATH': os.path.join(current_dir, '.glut', 'ffmpeg', 'bin'),
        # HuggingFace镜像源，下载模型时加速
        'HF_ENDPOINT': 'https://hf-mirror.com',
        # HuggingFace模型缓存目录
        'HF_HOME': os.path.join(current_dir, 'models'),
        # PyTorch模型缓存目录
        'TORCH_HOME': os.path.join(current_dir, 'models'),
        # ModelScope模型缓存目录
        'MODELSCOPE_CACHE': current_dir,
        # 禁用xformers的triton加速，避免兼容性问题
        'XFORMERS_FORCE_DISABLE_TRITON': '1',
        # ModelScope命令行工具路径
        'MODELSCOPE': os.path.join(current_dir, '.glut', 'Scripts', 'modelscope.exe')
    }
    # 作用：为后续主程序和依赖库提供必要的环境变量
    # 控制：模型加载、依赖库调用、音视频处理、镜像加速等功能

    # 3. 构建PATH环境变量，将自定义路径插入到PATH前面
    path_components = [
        env_vars['CU_PATH'],      # CUDA库路径，优先加载本地GPU库
        env_vars['SC_PATH'],      # 脚本路径，确保pip等工具可用
        env_vars['FFMPEG_PATH']   # FFMPEG路径，音视频处理可用
    ]
    # 作用：确保系统优先使用项目自带的依赖库和工具

    # 4. 获取当前系统PATH，并拼接自定义路径
    current_path = os.environ.get('PATH', '')
    new_path = os.pathsep.join(path_components + [current_path])
    env_vars['PATH'] = new_path
    # 作用：将自定义依赖路径插入PATH，保证依赖优先级
    # 控制：依赖库、工具的加载顺序

    # 5. 更新当前进程的环境变量
    os.environ.update(env_vars)
    # 作用：让后续启动的子进程（主程序）继承这些环境变量
    # 控制：主程序和其依赖的环境配置

    # 6. 显示启动提示
    print("启动中，请耐心等待 ")
    # 作用：告知用户程序正在启动

    try:
        # 7. 构建主程序启动命令
        python_exe = env_vars['PYTHON']  # Python解释器路径
        script_path = os.path.join('src', 'glut.py')  # 主程序脚本路径
        config_path = os.path.join('config', 'glut.yaml')  # 配置文件路径

        cmd = [python_exe, script_path, '--config', config_path]
        # 作用：准备以指定Python环境运行主程序，并加载配置文件
        # 控制：主程序的启动方式和配置来源

        # 8. 启动主程序
        result = subprocess.run(cmd, env=os.environ.copy())
        # 作用：以新进程方式运行主程序，继承当前环境变量
        # 控制：整个AI系统的启动入口

        # 9. 等待用户按键，防止窗口自动关闭
        input("按任意键继续...")

    except FileNotFoundError:
        # 10. 处理找不到Python解释器的异常
        print(f"错误：找不到Python解释器 {python_exe}")
        input("按任意键继续...")
    except Exception as e:
        # 11. 处理其他运行异常
        print(f"运行出错：{e}")
        input("按任意键继续...")

if __name__ == "__main__":
    main()
