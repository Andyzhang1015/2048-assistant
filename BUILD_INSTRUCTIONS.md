# 2048游戏辅助工具APK构建说明

## 概述

本说明文档介绍了如何将2048游戏辅助工具打包成Android APK文件。由于在Windows系统上直接使用Buildozer构建Android APK存在限制，我们提供了几种替代方案。

## 方案一：使用WSL (Windows Subsystem for Linux)

### 1. 安装WSL
```bash
wsl --install
```

### 2. 在WSL中安装必要依赖
```bash
sudo apt update
sudo apt install -y build-essential libffi-dev python3-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev git
```

### 3. 安装Python包
```bash
pip install kivy buildozer
```

### 4. 初始化Buildozer
```bash
buildozer init
```

### 5. 修改buildozer.spec文件
确保以下配置正确：
```
[app]
title = 2048游戏辅助工具
package.name = assistant2048
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,copy,os
orientation = portrait
```

### 6. 构建APK
```bash
buildozer android debug
```

## 方案二：使用GitHub Actions (推荐)

### 1. 创建.github/workflows目录
在项目根目录下创建`.github/workflows`目录。

### 2. 创建构建工作流文件
创建文件`.github/workflows/build-apk.yml`：

```yaml
name: Build APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install kivy buildozer

    - name: Initialize Buildozer
      run: |
        buildozer init

    - name: Build APK
      run: |
        buildozer android debug

    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: 2048-assistant-apk
        path: bin/*.apk
```

### 3. 提交并推送代码
```bash
git add .
git commit -m "Add GitHub Actions workflow for APK build"
git push
```

构建完成后，您可以在GitHub Actions的Artifacts部分下载APK文件。

## 方案三：使用Docker

### 1. 创建Dockerfile
创建文件`Dockerfile`：

```dockerfile
FROM ubuntu:20.04

RUN apt update && apt install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg8-dev \
    zlib1g-dev \
    git \
    python3 \
    python3-pip \
    openjdk-8-jdk

ENV ANDROID_HOME=/opt/android-sdk
WORKDIR /app

COPY . .

RUN pip3 install kivy buildozer

RUN buildozer init

CMD ["buildozer", "android", "debug"]
```

### 2. 构建Docker镜像
```bash
docker build -t 2048-assistant-builder .
```

### 3. 运行构建
```bash
docker run -v ${PWD}/bin:/app/bin 2048-assistant-builder
```

## 注意事项

1. 首次构建可能需要较长时间，因为需要下载Android SDK和NDK。
2. 确保您的系统有足够的磁盘空间（至少4GB）。
3. 构建过程中可能需要下载大量依赖，确保网络连接稳定。
4. 如果遇到权限问题，请检查文件权限设置。

## 故障排除

1. 如果构建失败，请检查日志中的错误信息。
2. 确保所有依赖库正确安装。
3. 检查buildozer.spec配置是否正确。
4. 如果遇到Java相关错误，请确保正确安装了JDK。

## APK文件位置

构建成功后，APK文件将位于项目根目录下的`bin`目录中，文件名类似于`assistant2048-*.apk`。