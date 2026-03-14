import os
import subprocess

def main():
    # 启动提示
    print("启动中，请耐心等待呀哈哈")

    # 获取当前目录
    current_dir = os.getcwd()

    # 设置环境变量
    env_vars = {
        "PYTHON": os.path.join(current_dir, ".glut", "python.exe"),
        "CU_PATH": os.path.join(current_dir, ".glut", "Lib", "site-packages", "torch", "lib"),
        "SC_PATH": os.path.join(current_dir, ".glut", "Scripts"),
        "FFMPEG_PATH": os.path.join(current_dir, ".glut", "ffmpeg", "bin"),
        "HF_ENDPOINT": "https://hf-mirror.com",
        "HF_HOME": os.path.join(current_dir, "models"),
        "TORCH_HOME": os.path.join(current_dir, "models"),
        "MODELSCOPE_CACHE": current_dir,
        "XFORMERS_FORCE_DISABLE_TRITON": "1",
        "MODELSCOPE": os.path.join(current_dir, ".glut", "Scripts", "modelscope.exe"),
    }

    # 拼接PATH
    path_components = [
        env_vars["CU_PATH"],
        env_vars["SC_PATH"],
        env_vars["FFMPEG_PATH"],
        os.environ.get("PATH", "")
    ]
    env_vars["PATH"] = ";".join(path_components)

    # 更新环境变量
    os.environ.update(env_vars)

    # 构建命令
    python_exe = env_vars["PYTHON"]
    script_path = os.path.join("src", "glut.py")
    config_path = os.path.join("config", "glut2.yaml")
    cmd = [python_exe, script_path, "--config", config_path]

    try:
        subprocess.run(cmd, env=os.environ.copy())
    except FileNotFoundError:
        print(f"错误：找不到Python解释器 {python_exe}")

    input("按任意键继续...")

if __name__ == "__main__":
    main()
