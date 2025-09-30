# 身份证 OCR 应用开发计划

## 1. 项目概述
- 构建一个基于 PaddleOCR 的中国身份证正反面识别服务，输出 HTTP API。
- 交付物包含：推理服务、Docker 镜像、开发环境部署脚本、前端测试页面、相关文档与自动化测试。

## 2. 技术选型与基础设施
- **OCR 引擎**：使用 PaddleOCR 作为底层依赖，首选 `paddleocr` Python SDK。
- **服务框架**：Python + FastAPI（支持异步 I/O、Swagger 文档、文件上传）。
- **模型与资源**：使用 PaddleOCR 内置中文识别模型，优化参数以适配身份证字体。
- **容器化**：基于官方 Python 镜像构建 Dockerfile，区分生产/开发配置（环境变量控制）。
- **依赖管理**：使用 `requirements.txt` 与 `pip`；在 Docker 中缓存依赖。
- **数据存储**：无持久化需求，所有处理在内存完成。

## 3. 系统架构与模块划分
1. `src/idcard_ocr/api`: FastAPI 路由、请求参数校验、响应模型。
2. `src/idcard_ocr/inference`: PaddleOCR 推理封装（加载模型、前后处理、字段提取）。
3. `src/idcard_ocr/schemas`: Pydantic 请求/响应定义，含正反面字段。
4. `src/idcard_ocr/utils`: 图片校验、临时文件管理、日志。
5. `tests/`: 单元测试、集成测试（API + OCR mock）。
6. `frontend/`: 轻量测试页面（HTML/JS）在容器外运行，通过 HTTP 调用服务。

## 4. 功能需求拆解
- **接口设计**：POST `/api/v1/idcard/parse`，表单/Multipart 接收 `front_image`、`back_image`；响应包含姓名、性别、出生日期、民族、住址、身份证号、签发机关、有效期限等字段，附带置信度。
- **业务逻辑**：自动识别图片正反面；调用 PaddleOCR，解析文本；正则或模板匹配提取字段；返回结构化 JSON。
- **异常处理**：缺失图片、文件过大、识别失败、字段缺失等，统一错误码和信息。
- **日志与监控**：基础日志输出（请求耗时、识别结果摘要）。

## 5. 开发里程碑
1. 初始化项目结构、依赖与基础配置。
2. 封装 PaddleOCR 驱动：加载模型、图像预处理、字段解析。
3. 实现 FastAPI 服务与响应模型。
4. 编写单元测试（字段提取）与 API 集成测试（利用脱敏样例）。
5. Dockerfile 与 docker-compose（dev 环境），包含服务启动脚本。
6. 本地调试并构建镜像，运行容器验证 API。
7. 部署 dev 环境（docker run/docker-compose），记录部署步骤。
8. 创建前端测试页面，调用 dev 服务验证输出。
9. 文档补充：README 更新、API 文档、部署指南。

## 6. 测试与质量保障
- **单元测试**：mock PaddleOCR 输出，验证字段解析逻辑、错误处理。
- **集成测试**：使用脱敏身份证样例图片，调用真实 PaddleOCR（可控制为慢速组）。
- **端到端验证**：通过测试页面上传图片确认结果。
- **覆盖率目标**：核心模块（解析、API）达到 ≥80%。

## 7. 容器与部署计划
- **Dockerfile**：多阶段构建（依赖安装 + 运行层），暴露端口 8080。
- **Entrypoint**：`uvicorn src.idcard_ocr.api:app --host 0.0.0.0 --port 8080`。
- **Dev 部署**：提供 `docker-compose.dev.yml`，挂载代码、启用热重载/日志。
- **环境变量**：`PADDLE_OCR_MODEL_DIR`、`LOG_LEVEL` 等；提供 `.env.example`。

## 8. 前端测试页面
- 使用纯 HTML/JS（Fetch API）上传正反面图片、展示 JSON 输出。
- 在宿主机或任意静态服务器运行，调用容器内的 API（支持自定义 API 地址）。

## 9. 风险与缓解措施
- **识别准确率**：收集多样化样本测试；必要时启用版式分析或自定义字典。
- **性能**：缓存 PaddleOCR 模型实例；限制并发请求数；提供超时处理。
- **隐私合规**：确保测试数据脱敏，避免将真实身份证信息入库或日志。

## 10. 后续工作与维护
- 计划添加 CI（GitHub Actions）执行 lint/test。
- 考虑引入 GPU/CPU 切换配置。
- 预留多语言拓展，支持其他证件类型。
