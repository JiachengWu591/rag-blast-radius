# CLAUDE.md

## 项目
完整架构、阶段划分、验收标准见 `PROJECT_SPEC.md`——开工前先完整读一遍。

## 环境
- Python 版本：3.12
- 包管理器：uv（`uv venv` 建虚拟环境，`uv pip install` 装依赖）
- 虚拟环境：`.venv`

## 模型与 API
- Provider：Deepseek，走 OpenAI 兼容接口——用官方 `openai` Python 包，`base_url` 指向 `https://api.deepseek.com`
- API key 环境变量名：`DEEPSEEK_API_KEY`——代码里只引用这个变量名，绝不写死真实值
- 生成 Agent 默认模型：`deepseek-chat`；如果回答质量不够，换成 `deepseek-reasoner`
- 结构化输出用 `tool_choice` 强制工具的方式（`{"type": "function", "function": {"name": ...}}`，见 PROJECT_SPEC.md 第 3.3 节）

## 约定
- 代码风格：强制 type hints——所有函数签名（参数、返回值）都要写类型注解
- 提交习惯：一个 Phase 一次 commit，message 格式 "Phase N: xxx"

## 永远
- 每个 Phase 完成先给我看，等我确认再继续下一个（见 PROJECT_SPEC.md 0.5）
- 任何校验失败，默认返回"没有找到相关信息"，不放行（fail-closed）
- 检索结果稀薄时绝不自动放宽租户过滤范围去补足结果
- 绝不把真实密钥写进任何文件
