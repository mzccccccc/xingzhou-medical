# CLAUDE.md — dev 仓库记忆索引

本仓库(xingzhou 的医学影像项目)结构:
- `backend/` — Python 后端(uv 管理): NIfTI→DICOM 转换、上传 Orthanc 等
- `ohif/` — OHIF Viewer 前端(源自上游 `OHIF/Viewers` 的 `release/3.13`,
  已并入本仓库, 排除 `node_modules`)
- `docx/` — 计划与文档; 进展记录在 `docx/plan/{backend,frontend}/已办事项.md`

Git 采用**单一仓库**: backend、ohif 原本各自的独立 `.git` 已删除, 统一由 dev 仓库跟踪。

## 记忆文件(通过 @ 导入, 每次会话自动加载)

@.claude/memory/git-commit-workflow.md

@.claude/memory/yiban-shixiang.md
