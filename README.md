# PhotoVideoTimeSort 📸⏳
[English Version](#english-version)

## 智能媒体文件整理专家

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Open Source](https://img.shields.io/badge/Open%20Source-✓-success)

### ✨ 核心功能
- **四维时间追溯**：EXIF元数据 > 视频创建时间 > 文件名时间 > 文件系统时间
- **智能路径生成**：`年/年-月/类型/年月日-指纹-地点.扩展名`
- **军用级去重**：基于MD5哈希的精确重复检测
- **地理位置解析**：支持GPS坐标转中文地址（通过OpenStreetMap）
- **格式兼容性**：全面支持HEIC/HEIF等苹果生态格式

### 📦 快速安装
```bash
git clone https://github.com/yourname/PhotoVideoTimeSort.git
cd PhotoVideoTimeSort
pip install -r requirements.txt
```

### 🚀 使用指南

```

# 基础整理（输出到./organized目录）
python PhotoVideoTimeSort.py -i ~/照片库 -o ./organized

# 强制指定地点（适合无GPS信息的旧照片）
python PhotoVideoTimeSort.py -i ~/老照片 -L "北京四合院" -o ./nostalgia
```


### 🧠 时间解析策略

| 优先级 | 来源                  | 示例格式                  |
| ------ | --------------------- | ------------------------- |
| 1      | EXIF DateTimeOriginal | 2023:12:31 23:59:59       |
| 2      | 视频CreationTime      | 2023-12-31T23:59:59.999Z  |
| 3      | 文件名                | IMG_20231231_235959.jpg   |
| 4      | 文件系统时间          | 取自ctime/mtime的较早时间 |

### 🤝 参与贡献

欢迎通过Issue或PR参与：

1. Fork仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起Pull Request
