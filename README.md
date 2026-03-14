# OpenAvatarChat 修改补丁

这是 [OpenAvatarChat](https://github.com/OpenAvatarChat/OpenAvatarChat) 的修改补丁仓库。

## 📦 使用方法

由于原项目包含大量模型文件（超过 GitHub 1GB 限制），本仓库只包含**修改的代码文件**。

### 步骤 1：下载原项目

```bash
git clone https://github.com/OpenAvatarChat/OpenAvatarChat.git
cd OpenAvatarChat
```

### 步骤 2：应用本仓库的修改

```bash
# 方法 1：使用 git（推荐）
git remote add patch https://github.com/CAIZHIYU2333/B606-shuziporolr.git
git fetch patch
git merge patch/master --allow-unrelated-histories

# 方法 2：手动复制
# 将本仓库的 src/ 目录覆盖到原项目
```

### 步骤 3：下载模型文件

参考原项目的模型下载说明。

## 📝 修改内容

### 代码修改
- `src/handlers/vad/silerovad/silero_vad/src/silero_vad/data/__init__.py` - 修复导入问题
- 子模块改为普通文件夹（无需额外克隆）

### 配置修改
- `.gitignore` - 排除大型模型文件

## ⚠️ 注意事项

1. **本仓库不是完整项目** - 必须先下载原项目
2. **模型文件需自行下载** - 参考原项目的模型下载说明

## 🔗 相关链接

- 原项目：https://github.com/OpenAvatarChat/OpenAvatarChat
- 本仓库：https://github.com/CAIZHIYU2333/B606-shuziporolr.git
