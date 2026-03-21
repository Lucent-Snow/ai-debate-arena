# Testing Strategy

## 基本原则

- 测试必须走真实接口
- 不使用 mock、fake response、伪造 transport
- 所有自动化验证都要明确依赖的外部条件

## 当前待确认信息

在完整实现前，至少要先确认：

- `base_url` 是否兼容 OpenAI API
- 可用 `model` 名称是什么
- 模型是否支持多轮 `messages`
- 模型是否支持稳定的 JSON 输出
- 接口是否有限流、超时、并发限制

## 当前已验证结论

- `https://dashscope.aliyuncs.com/compatible-mode/v1` 兼容 OpenAI 风格的 `models` 和 `chat/completions`
- `qwen-plus` 直连延迟明显低于前面的中转接口，适合作为默认测试模型
- `response_format={"type":"json_object"}` 可用，但真实模型仍可能因输出过长导致 JSON 被截断
- 项目实现里已经加入 judge JSON 的压缩与二次兜底，以适配真实接口的不稳定结构化输出

## 计划中的验证层次

### 1. 连通性测试

目标：

- 验证认证头是否正确
- 验证模型列表接口是否可用
- 验证聊天接口基础请求是否可用

### 2. 最小辩论流程测试

目标：

- 跑通 1v1 最小轮数
- 检查 topic、events、judging、summary 是否都有产出
- 检查输出 JSON 是否满足约定字段

### 3. 完整模式测试

目标：

- 跑通 4v4 固定 4 轮
- 验证 coach、debater、judge、summarizer 事件完整性
- 验证可见性字段、round 编号和 agent 标识是否正确

### 4. Viewer 验证

目标：

- 静态页面可加载导出的 JSON
- 页面能展示核心信息块
- 桌面端和移动端都可用

## 建议环境变量

- `AI_DEBATE_BASE_URL`
- `AI_DEBATE_API_KEY`
- `AI_DEBATE_MODEL`

## 现实约束

- 真实接口测试成本更高，耗时更长，也更容易受外部服务波动影响
- 如果接口输出不稳定，测试需要以“契约字段存在 + 关键流程完成”为验收重点，而不是要求每次文案完全一致
- 在没有确认模型名之前，不能定义最终自动化测试命令
