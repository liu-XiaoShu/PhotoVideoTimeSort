# PhotoVideoTimeSort 📸⏳
[简体中文版本](#https://github.com/liu-XiaoShu/PhotoVideoTimeSort/blob/main/README.md)


## Intelligent Media Organizer

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Open Source](https://img.shields.io/badge/Open%20Source-✓-success)

### ✨ Core Features
- **Four-stage Time Tracing**: EXIF metadata > Video creation time > Filename timestamp > Filesystem time
- **Smart Path Generation**: `Year/Year-Month/Type/YYYY-MM-DD-Fingerprint-Location.ext`
- **Military-grade Deduplication**: MD5 hash-based exact duplicate detection
- **Geolocation Parsing**: Convert GPS coordinates to Chinese addresses (via OpenStreetMap)
- **Format Compatibility**: Full support for Apple ecosystem formats (HEIC/HEIF)

### 📦 Quick Installation
```bash
git clone https://github.com/yourname/PhotoVideoTimeSort.git
cd PhotoVideoTimeSort
pip install -r requirements.txt
```

### 🚀 Usage Guide

```

# Basic organization (output to ./organized directory)
python PhotoVideoTimeSort.py -i ~/Photos -o ./organized

# Force location metadata (for old photos without GPS)
python PhotoVideoTimeSort.py -i ~/Old_Photos -L "Beijing Courtyard" -o ./nostalgia
```

### 🧠 Time Resolution Strategy

| Priority | Source                | Example Format           |
| -------- | --------------------- | ------------------------ |
| 1        | EXIF DateTimeOriginal | 2023:12:31 23:59:59      |
| 2        | Video CreationTime    | 2023-12-31T23:59:59.999Z |
| 3        | Filename Timestamp    | IMG_20231231_235959.jpg  |
| 4        | Filesystem Time       | Earlier of ctime/mtime   |

### 🤝 Contributing

We welcome contributions through Issues or PRs:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
