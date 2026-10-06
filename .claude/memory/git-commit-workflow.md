# 记忆: Git 提交工作流(每次提交必须遵守)

## 何时提交
- **绝不主动提交**。只有用户明确说"提交 / commit / push"时才执行 git 操作。
- 用户会在每次提交前, 先更新 `docx/plan/` 下的 `已办事项.md`。

## 生成 commit message 的步骤
1. 提交前先读取(存在才读, 不存在跳过):
   - `docx/plan/backend/已办事项.md`
   - `docx/plan/frontend/已办事项.md`
2. 依据每条更新的**时间**与**连续编号**, 判断"本次最新完成的事项"
   —— 即: 最近一次更新时间所对应、编号最大的那批条目。
3. 据此**精炼**概括出 `commit -m`, 只反映本次实际完成的工作;
   不要照抄整段文档, 不要罗列历史全部事项。
4. message 用中文, 简洁准确。
   示例风格: `完成后端 NIfTI→DICOM 转换并上传 Orthanc`

## 提交范围与约定
- 提交整个 dev 仓库(backend + ohif + docx), 自动排除 `.gitignore` 忽略项。
- backend、ohif 已并入 dev 单一仓库, 不再有子仓库/嵌入式仓库。
- 提交信息末尾附环境要求的署名行:
  `Co-Authored-By: Claude Code <noreply@anthropic.com>`

## 注意
- 首次提交前确认作者身份正确(user.name 不应含多余引号)。
- 若涉及推送到远端(GitHub/GitLab), 先与用户确认远端地址与分支。
