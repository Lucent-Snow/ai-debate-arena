# AI Debate Arena

## 技术栈
- Python 3.10+，CLI 使用 `typer`
- LLM 调用使用 `httpx`
- 测试编排使用 `pytest`
- 静态前端在 `web/`，无构建步骤

## 目录结构
- `debate/`：后端核心实现，包含配置、agent、编排、输出
- `web/`：静态 JSON 查看器
- `examples/`：示例配置与样例输出
- `tests/`：自动化验证脚本
- `docs/`：架构、约束、测试说明

## 开发命令
- 安装：`pip install -e .[dev]`
- 测试：`pytest`
- lint：`ruff check .`
- 启动 CLI：`debate --help`
- 启动查看器：`debate serve --port 8080`

## 模块边界
- `debate/agents/` 只负责 agent 行为、上下文构造、调用 LLM
- `debate/engine/` 负责 debate 生命周期、事件记录、1v1 / 4v4 流程编排
- `debate/output/` 负责 CLI 展示和 JSON 导出
- `web/` 只消费导出的 JSON，不依赖 Python 运行时
- `tests/` 只做黑盒或近黑盒验证，不在测试代码里复制业务实现

## 验证方式
- 不接受 mock，不接受 fake transport，不接受伪造 LLM 返回
- 自动化测试默认直接调用真实接口，所需信息通过环境变量或测试配置注入
- 测试重点覆盖：接口连通性、1v1 流程、4v4 流程、JSON 导出契约、静态 viewer 读取结果
- 如果真实接口能力不足以稳定输出结构化 JSON，先在 `docs/` 写清限制，再决定是否进入实现

## 配置约定
- 不把真实密钥硬编码进仓库
- 模型名、`base_url`、`api_key` 通过 YAML 配置和环境变量组合提供
- 默认先按 OpenAI-compatible 接口设计，若探测结果不同，需要先更新 `docs/testing.md`
