# 低代码 DSL 回归用例（fixtures）

用于防止 `workflowContext` 等节点「凭空造字段名」、任务模式误判、确认来源无证据等问题复发。
配套校验逻辑见 `scripts/field_schema.py`、`scripts/validate_yml.py`、`scripts/validate_ir.py`。

## 用例

| 文件 | 预期 `validate_yml.py` 结果 |
|------|------------------------------|
| `workflow_context_bad.workflow.yml` | **错误数 = 8**（必须非 0） |
| `workflow_context_good.workflow.yml` | **错误数 = 0**（`--strict` 下警告也为 0） |

| 文件 | 预期 `validate_ir.py` 结果 |
|------|----------------------------|
| `asset_fast_workflow_good.ir.yml` | **通过**：workflow-only 保持 `asset-fast`，且有确认/仓库证据 |
| `workflow_update_existing_good.ir.yml` | **通过**：修改已有 workflow 时有目标流程证据和纠偏记录 |
| `whole_app_mode_ambiguous_bad.ir.yml` | **失败**：不能只因用户提供 `apptag` 就升级为 `whole-app` |
| `workflow_confirmation_evidence_bad.ir.yml` | **失败**：workflow confirmation 不能裸写 `source: user_confirmed` |

`bad` 用例来自真实模型产物 `请假审批流程.workflow.yml`：`workflowContext` 被写成
`contextguid/contextname/contexttext/ordernum`（捏造名），且缺必填 `belongto/fieldtype`，
`fieldname` 值也写错（应为 `leave_days` 以匹配条件里的 `[#=leave_days#]`）。

## bad 用例必须命中的 8 条 error

1. `workflowContext[0]` 字段 `contextguid` 应为 `fieldguid`
2. `workflowContext[0]` 字段 `contextname` 应为 `fieldname`
3. `workflowContext[0]` 字段 `contexttext` 应为 `note`
4. `workflowContext[0]` 字段 `ordernum` 不属于本节点，应删除
5. `workflowContext[0]` 缺少必填字段 `belongto`
6. `workflowContext[0]` 缺少必填字段 `fieldtype`
7. `transition[2].workflowTransitionCondition[0].leftvalue` 引用的 `[#=leave_days#]` 未在 `workflowContext.fieldname` 中定义
8. `transition[3].workflowTransitionCondition[0].leftvalue` 引用的 `[#=leave_days#]` 未在 `workflowContext.fieldname` 中定义

## 运行

```bash
# 应为 8 个 error（退出码非 0）
python3 scripts/validate_yml.py evals/fixtures/workflow_context_bad.workflow.yml

# 应为 0 error（退出码 0），--strict 下 0 warn
python3 scripts/validate_yml.py --strict evals/fixtures/workflow_context_good.workflow.yml

# IR 正例应通过
python3 scripts/validate_ir.py evals/fixtures/asset_fast_workflow_good.ir.yml
python3 scripts/validate_ir.py evals/fixtures/workflow_update_existing_good.ir.yml

# 修改已有 workflow dry-run：必须保留 processguid/processversionguid/version
python3 scripts/update_workflow.py \
  --workflow-file evals/fixtures/workflow_context_good.workflow.yml \
  --from-ir evals/fixtures/workflow_update_existing_good.ir.yml \
  --asset-id asset-workflow-update-001 \
  --dry-run

# IR 反例应失败
python3 scripts/validate_ir.py evals/fixtures/whole_app_mode_ambiguous_bad.ir.yml
python3 scripts/validate_ir.py evals/fixtures/workflow_confirmation_evidence_bad.ir.yml
```

> `good` 与 `bad` 仅 `workflowContext` 一段不同，便于对照「错误字段名 → 正确字段名」。
