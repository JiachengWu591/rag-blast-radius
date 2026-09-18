# CLAUDE.md

## 项目
完整架构、阶段划分、验收标准见 `PROJECT_SPEC.md`——开工前先完整读一遍。

## 环境
- Python 版本：[你本地的版本]
- 包管理器：[pip / poetry / uv]
- 虚拟环境：[还没建 / 已经建在 ./venv]

## 模型与 API
- Provider：Claude（Anthropic），官方 `anthropic` Python 包
- API key 环境变量名：`ANTHROPIC_API_KEY`——代码里只引用这个变量名，绝不写死真实值
- 生成 Agent 默认模型：`claude-haiku-4-5-20251001`；如果回答质量不够，换成 `claude-sonnet-5`
- 结构化输出用 `tool_choice` 强制工具的方式（见 PROJECT_SPEC.md 第 3.3 节）

## 约定
- 代码风格：[比如要不要强制 type hints]
- 提交习惯：一个 Phase 一次 commit，message 格式 "Phase N: xxx"

## 永远
- 每个 Phase 完成先给我看，等我确认再继续下一个（见 PROJECT_SPEC.md 0.5）
- 任何校验失败，默认返回"没有找到相关信息"，不放行（fail-closed）
- 检索结果稀薄时绝不自动放宽租户过滤范围去补足结果
- 绝不把真实密钥写进任何文件
