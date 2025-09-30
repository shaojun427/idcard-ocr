# idcard-ocr

基于 PaddleOCR 的中国身份证识别服务，提供 HTTP API 与示例前端用于验证识别结果。

# AI
项目下已有plan和init文件，支持ai工具修改优化

## 功能特性
- FastAPI 实现的 `/api/v1/idcard/parse` 接口，支持身份证正反面图片上传。
- 返回姓名、性别、出生日期、民族、住址、身份证号、签发机关、有效期限等字段及置信度。
- 提供 `frontend/index.html` 测试页面，可直接上传图片验证接口输出。
- 完整 Dockerfile 与 `docker-compose.dev.yml`，支持本地与部署环境运行。

## 快速开始
```bash
python3 -m venv .venv && source .venv/bin/activate
make install
uvicorn idcard_ocr.api.app:app --host 0.0.0.0 --port 8080 --reload
```
服务启动后可以访问 `http://127.0.0.1:8080/docs` 查看 Swagger 文档。

## Docker 运行
```bash
docker build -t idcard-ocr:latest .
docker run --d --name idcard-ocr-api -p 8080:8080 idcard-ocr:latest
```
若此前运行过容器需重新部署
```bash
docker stop idcard-ocr-api
docker rm idcard-ocr-api
docker run --rm --name idcard-ocr-api -p 8080:8080 idcard-ocr:latest
```
可先执行 ``，或在启动时省略 `--rm` 保留容器以便调试。

或通过 Make 命令：
```bash
make docker-build
make docker-run | make docker-restart
```
开发模式可使用：
```bash
make dev-up
```
该命令会在本地以热更新方式运行 API 服务，供前端页面或自动化测试调用。

## 前端自测页面
前端示例页面位于 `frontend/index.html`，请在宿主机运行静态服务器或直接使用浏览器打开：
```bash
python3 -m http.server 8001 --directory frontend
```
然后在浏览器打开 <http://127.0.0.1:8001/index.html>，将 API 地址设置为 `http://127.0.0.1:8080/api/v1/idcard/parse`，即可在 Docker 容器外部验证服务能力。

## 测试
```bash
make test
```

## 环境变量
- `PADDLE_OCR_DET_MODEL_DIR` / `PADDLE_OCR_REC_MODEL_DIR` / `PADDLE_OCR_CLS_MODEL_DIR`：自定义模型目录。
- `PADDLE_OCR_USE_GPU`：设置为 `true`/`1` 启用 GPU（需对应环境支持）。
- `LOG_LEVEL`：控制日志级别。

## 部署资源建议
- **最小配置**：2 vCPU、8 GB 内存，磁盘预留 ≥10 GB（镜像约 3 GB，模型及缓存约 2 GB，加上日志和系统空间）。
- **推荐配置（面向实时 API）**：4 vCPU 以上、16 GB 内存、磁盘预留 ≥20 GB，可降低冷启动和推理延迟。
- **GPU 依赖**：PaddleOCR 在 CPU 环境下可正常工作；GPU 并非必需，但若部署在具备 CUDA 的服务器并设置 `PADDLE_OCR_USE_GPU=true`，可显著提升批量识别速度。
- **其它注意事项**：保持 1–2 GB 空闲内存供操作系统及负载波动使用，并定期清理 `/root/.paddleocr` 下载的模型缓存。
