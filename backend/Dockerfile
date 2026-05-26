FROM python:3.10

WORKDIR /app

# 安装OpenCV所需的系统库依赖（不含libGL，使用headless版本替代）
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y opencv-python 2>/dev/null || true && \
    pip install --no-cache-dir opencv-python-headless
# 确保opencv-python-headless存在（ultralytics可能拉取opencv-python覆盖它）

COPY . .

# 最终确保opencv-python-headless存在（防止ultralytics拉取opencv-python）
RUN pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true && \
    pip install --no-cache-dir "numpy<2" "opencv-python-headless==4.8.1.78"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]