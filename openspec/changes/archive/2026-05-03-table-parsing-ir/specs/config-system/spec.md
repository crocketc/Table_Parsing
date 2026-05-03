## ADDED Requirements

### Requirement: ParseConfig 数据类
系统 SHALL 提供 ParseConfig dataclass 作为解析配置的统一载体。

#### Scenario: 默认配置
- **WHEN** 不传入任何配置参数创建 ParseConfig
- **THEN** 所有功能开关使用安全默认值（extract_media=False、chunk_size=None、encoding_detection=True）

#### Scenario: 自定义配置
- **WHEN** 创建 ParseConfig(encoding="gbk", extract_media=True, chunk_size=5000)
- **THEN** 各字段值正确设置，后续解析行为遵循该配置

### Requirement: 编码探测开关
系统 SHALL 支持通过配置关闭自动编码探测。

#### Scenario: 启用编码探测（默认）
- **WHEN** ParseConfig.encoding_detection 为 True（默认）
- **THEN** CSV 解析时自动进行编码探测

#### Scenario: 禁用编码探测
- **WHEN** ParseConfig.encoding_detection 为 False
- **THEN** CSV 解析时不进行编码探测，使用 ParseConfig.encoding 指定的编码（默认 UTF-8）

### Requirement: 多媒体提取开关
系统 SHALL 支持通过配置控制是否提取嵌入的多媒体对象。

#### Scenario: 关闭媒体提取（默认）
- **WHEN** ParseConfig.extract_media 为 False（默认）
- **THEN** Cell.embedded_media 始终为 None，不提取任何图片或图表

#### Scenario: 开启媒体提取
- **WHEN** ParseConfig.extract_media 为 True
- **THEN** 系统提取嵌入的图片和图表，存入 Cell.embedded_media

### Requirement: 大文件分块配置
系统 SHALL 支持通过配置指定 CSV 分块大小。

#### Scenario: 指定分块大小
- **WHEN** ParseConfig.chunk_size 为 10000
- **THEN** CSV 解析器每次产出最多 10000 行的 IR 块

#### Scenario: 不分块
- **WHEN** ParseConfig.chunk_size 为 None（默认）
- **THEN** 全量读取，返回单个 Workbook

### Requirement: 指定编码
系统 SHALL 支持用户显式指定 CSV 文件的编码。

#### Scenario: 显式指定编码
- **WHEN** ParseConfig.encoding 为 "gbk"
- **THEN** 系统跳过编码探测，直接使用 GBK 编码解析

#### Scenario: 自动编码（默认）
- **WHEN** ParseConfig.encoding 为 None（默认）
- **THEN** 系统自动进行编码探测

### Requirement: 模型 API 配置
系统 SHALL 支持配置多模态模型的 API 端点、模型名称、API Key 和并发数，用于媒体内容的 AI 理解。

#### Scenario: 默认模型配置
- **WHEN** 不指定任何模型参数创建 ParseConfig
- **THEN** model_api 默认配置为：base_url="http://169.254.83.107:1234"、model="qwen3.5-4b"、api_key=""、max_concurrency=6

#### Scenario: 自定义模型端点
- **WHEN** 创建 ParseConfig(model_api=ModelApiConfig(base_url="https://api.openai.com/v1", model="gpt-4o", api_key="sk-xxx"))
- **THEN** 系统使用指定的端点和模型进行多模态调用

#### Scenario: 并发数控制
- **WHEN** ParseConfig.model_api.max_concurrency 为 3
- **THEN** 多媒体 AI 理解同时最多发起 3 个并发请求

#### Scenario: 空 API Key
- **WHEN** ParseConfig.model_api.api_key 为空字符串（默认）
- **THEN** 系统在调用模型 API 时不发送 Authorization 头或发送空 Key（取决于目标 API 规范）

### Requirement: ModelApiConfig 数据类
系统 SHALL 提供 ModelApiConfig dataclass 封装模型 API 相关配置。

#### Scenario: ModelApiConfig 字段完整性
- **WHEN** 创建 ModelApiConfig
- **THEN** 包含 base_url（str）、model（str）、api_key（str）、max_concurrency（int）四个字段

#### Scenario: ModelApiConfig 安全默认值
- **WHEN** 无参创建 ModelApiConfig
- **THEN** base_url="http://169.254.83.107:1234"、model="qwen3.5-4b"、api_key=""、max_concurrency=6

### Requirement: 模型 API 遵循 OpenAI 通用接口
系统 SHALL 通过 OpenAI Chat Completions 兼容协议调用模型，确保可无缝对接 LM Studio、Ollama、vLLM、Azure OpenAI、OpenAI 官方等任何兼容端点。

#### Scenario: 请求格式兼容
- **WHEN** 系统向模型 API 发送请求
- **THEN** 请求格式遵循 OpenAI Chat Completions API 规范：POST `{base_url}/v1/chat/completions`，body 包含 `model`、`messages`、可选 `max_tokens`

#### Scenario: 图片通过 base64 内联传递
- **WHEN** 向模型发送包含图片的请求
- **THEN** 图片以 base64 编码通过 `image_url` 类型的 message content 传递，符合 OpenAI Vision API 格式

#### Scenario: 响应格式解析
- **WHEN** 模型返回响应
- **THEN** 系统解析 `choices[0].message.content` 字段作为理解结果
