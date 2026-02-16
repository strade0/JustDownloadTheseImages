# Just Download these Images

## 📥 Download

Grab the latest `.exe` from the [**Releases**](../../releases/latest) page — no installation required.

A lightweight Windows desktop app that collects images from your clipboard and batch-downloads them as JPEGs.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)

## ✨ Features

- **Paste from clipboard** — Copy any image in your browser (right-click → Copy Image) and press `Ctrl+V` to add it
- **Click to remove** — Hover over a thumbnail and click to remove it
- **Batch download** — Save all images as high-quality JPEGs to any folder in one click

## 📥 Download

Grab the latest `.exe` from the [**Releases**](../../releases/latest) page — no installation required.

## 🛠️ Build from Source

**Requirements:** Python 3.8+ and pip

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/JustDownloadTheseImages.git
cd JustDownloadTheseImages

# Install dependencies
pip install -r requirements.txt

# Run directly
python image_collector.py

# Or build the .exe
pyinstaller ImageCollector.spec --clean
# Output: dist/JustDownloadTheseImages.exe
```

## 📋 Project Structure

```
├── image_collector.py    # Main application
├── icon.ico              # App icon
├── ImageCollector.spec   # PyInstaller build config
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
└── README.md
```

## 📄 License

[MIT](LICENSE) — use it however you like.


