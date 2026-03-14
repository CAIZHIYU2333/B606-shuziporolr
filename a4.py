import os  # 导入os模块，用于与操作系统进行交互，如路径操作、环境变量设置等
import subprocess  # 导入subprocess模块，用于创建新进程、执行外部命令
import sys  # 导入sys模块，常用于系统相关操作（本脚本未直接用到）

def main():
    """主函数：设置环境变量并运行主程序"""

    # 获取当前工作目录，os.getcwd()返回当前Python进程的工作目录
    current_dir = os.getcwd()

    # 构建需要设置的环境变量字典
    env_vars = {
        # 'PYTHON'：指定Python解释器路径，位于当前目录下的.glut/python.exe
        'PYTHON': os.path.join(current_dir, '.glut', 'python.exe'),
        # 'CU_PATH'：CUDA库路径，torch的lib目录，供PyTorch等依赖查找CUDA动态库
        'CU_PATH': os.path.join(current_dir, '.glut', 'Lib', 'site-packages', 'torch', 'lib'),
        # 'SC_PATH'：Scripts目录，包含可执行脚本（如pip、modelscope等）
        'SC_PATH': os.path.join(current_dir, '.glut', 'Scripts'),
        # 'FFMPEG_PATH'：ffmpeg的可执行文件目录，供音视频处理调用
        'FFMPEG_PATH': os.path.join(current_dir, '.glut', 'ffmpeg', 'bin'),
        # 'HF_ENDPOINT'：huggingface镜像源地址，加速模型下载
        'HF_ENDPOINT': 'https://hf-mirror.com',
        # 'HF_HOME'：huggingface模型缓存目录，指定为当前目录下models
        'HF_HOME': os.path.join(current_dir, 'models'),
        # 'TORCH_HOME'：PyTorch模型缓存目录，指定为当前目录下models
        'TORCH_HOME': os.path.join(current_dir, 'models'),
        # 'MODELSCOPE_CACHE'：ModelScope模型缓存目录，指定为当前工作目录
        'MODELSCOPE_CACHE': current_dir,
        # 'XFORMERS_FORCE_DISABLE_TRITON'：禁用xformers的triton加速，避免兼容性问题
        'XFORMERS_FORCE_DISABLE_TRITON': '1',
        # 'MODELSCOPE'：modelscope可执行文件路径，供后续脚本调用
        'MODELSCOPE': os.path.join(current_dir, '.glut', 'Scripts', 'modelscope.exe')
    }

    # 需要添加到PATH环境变量的目录列表
    path_components = [
        env_vars['CU_PATH'],      # CUDA库路径，确保PyTorch等能找到相关动态库
        env_vars['SC_PATH'],      # Scripts目录，确保可执行脚本可被系统识别
        env_vars['FFMPEG_PATH']   # ffmpeg可执行文件目录，供音视频处理调用
    ]

    # 获取当前系统PATH环境变量
    current_path = os.environ.get('PATH', '')
    # 将自定义路径与原有PATH拼接，os.pathsep为分隔符（Windows下为;，Linux下为:）
    new_path = os.pathsep.join(path_components + [current_path])
    # 将新PATH写入env_vars，后续用于更新环境变量
    env_vars['PATH'] = new_path

    # 更新当前进程的环境变量，os.environ.update会将env_vars中的键值对写入系统环境
    os.environ.update(env_vars)

    # 打印启动提示信息，告知用户程序正在启动
    print("启动中，请耐心等待 ")

    try:
        # 获取Python解释器路径
        python_exe = env_vars['PYTHON']
        # 构建主程序脚本路径，假设主程序为src/glut2.py
        script_path = os.path.join('src', 'glut2.py')

        # 构建命令行参数列表，指定用自定义Python解释器运行主脚本
        cmd = [python_exe, script_path]

        # 使用subprocess.run执行命令，env参数传递当前进程的环境变量副本
        result = subprocess.run(cmd, env=os.environ.copy())

        # 主程序运行结束后，等待用户按任意键继续，防止窗口自动关闭
        input("按任意键继续...")

    except FileNotFoundError:
        # 如果找不到Python解释器，输出错误信息并等待用户操作
        print(f"错误：找不到Python解释器 {python_exe}")
        input("按任意键继续...")
    except Exception as e:
        # 捕获其他异常，输出错误信息并等待用户操作
        print(f"运行出错：{e}")
        input("按任意键继续...")

# 判断当前脚本是否为主程序入口
if __name__ == "__main__":
    main()
