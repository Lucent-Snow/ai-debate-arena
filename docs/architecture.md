# Architecture Notes

## 目标

按 PRD 落地一个 CLI-first 的 AI 辩论系统，包含：

- 1v1 模式
- 4v4 模式
- 多角色 agent：debater、coach、judge、summarizer
- 统一事件日志
- JSON 导出
- 静态 Web 查看器

## 模块划分

### `debate/config.py`

负责：

- 读取 YAML 配置
- 解析环境变量
- 解析多层级模型覆盖关系

不负责：

- 发起 LLM 请求
- 参与辩论流程控制

### `debate/models.py`

负责：

- 定义基础数据结构
- 约束 JSON 导出格式
- 表达 event、topic、judge score、agent config 等领域模型

### `debate/agents/`

负责：

- 组装各角色 prompt
- 基于可见性规则构造上下文
- 调用统一 LLM client

不负责：

- 决定整场辩论阶段流转

### `debate/engine/`

负责：

- 组织 1v1 / 4v4 生命周期
- 记录事件日志
- 按 phase 驱动不同 agent
- 生成最终结果对象

### `debate/output/`

负责：

- CLI 格式化输出
- 序列化 JSON 结果

### `web/`

负责：

- 读取导出的 JSON
- 可视化 topic、agents、events、judging、summary、stats

不负责：

- 实时通信
- 直接调用 LLM

## 关键边界

- 事件日志是单一事实来源，前端只读结果 JSON，不反向影响后端
- 真实接口能力决定 JSON 结构化输出方案；如果接口不支持严格 JSON mode，需要先定义重试与容错策略
- v1 不做流式输出、不做 RAG、不做持久化历史
