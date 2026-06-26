---
name: lowcode-gen-event
description: Epoint 低代码动作流原子生成器。根据 lowcode-dsl-gen IR 的 event asset 生成 event/*.event.yml；负责动作流触发、标准三段式 Webhook、业务动作、context class、Webhook URL 和 check_dsl 校验。标准 CRUD 不主动生成 event。
---

# lowcode-gen-event

只处理 `assets[type=event]`。动作流计划写入 `.lowcode-plans/<apptag>/event/<asset-id>-plan.md`。

## Input 输入

```yaml
spec:
  name: "提交后状态联动"
  sign: "submitStatus"
  triggerType: "webhook"
  apptag: "purchaseproject"
  bizAction: "PurchaseProjectRestService_submitStatus"
  bizTitle: "提交并更新状态"
  contextClass: "com.epoint.purchaseproject.context.PurchaseProjectContext"
  webhookUrl: ""
  nodes: []
```

## References 参考文档

- `../../references/event/动作流/index.md`
- `../../references/event/动作流/基础结构/三段式骨架.md`
- `../../references/event/动作流/检查清单/六大检查清单.md`
- `../../references/event/动作流/常见错误/常见错误与禁止事项.md`

## Steps 执行步骤

1. 确认用户明确要求了 event / 动作流，或该 IR 来自 workflow ruleguid 依赖。
2. 拒绝误生成 CRUD event，除非用户明确要求且计划已标记为非标准。
3. 写入/更新 `.lowcode-plans/<apptag>/event/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、check_dsl 结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 用以下命令转换标准 event IR：
   ```bash
   python3 ../../scripts/ir_to_event_args.py <ir.yml> --asset-id <asset-id>
   ```
5. 落盘前先 dry-run：
   ```bash
   python3 ../../scripts/add_event.py --from-ir <ir.yml> --asset-id <asset-id> --app-root <app-root> --dry-run
   ```
6. 批准后去掉 `--dry-run` 再执行。
7. 校验：
   ```bash
   python3 ../../scripts/check_dsl.py <event-file>
   python3 ../../scripts/validate_yml.py <event-file>
   ```

## Red Lines 红线

- 标准 list/detail/save/delete 不需要 event。
- 不臆造业务动作名（business action）或 context class。
- 高级分支/循环/代码节点 event 必须先读对应的 event references，并记录六大检查。
