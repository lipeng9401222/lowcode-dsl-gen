---
name: lowcode-gen-page
description: Epoint 低代码页面设计器原子生成器。根据 lowcode-dsl-gen IR 的 pagedesigne asset 生成 page/*.json，负责页面标题、pagetag、device、pageType、endpoint、字段、查询条件和引用闭合；默认 desktop，只有用户明确移动端/H5/小屏时使用 mobile。
---

# lowcode-gen-page

只处理 `assets[type=pagedesigne]`。

## Input

```yaml
spec:
  title: "采购立项列表"
  pagetag: "purchaseproject_list"
  device: "desktop"
  pageType: "list"
  endpoint: "/api/purchaseproject"
  fields: []
  query: []
```

## References

- Main entry: `../../references/page/页面设计器/index.md`
- Generation and validation: `../../references/page/页面设计器/生成与校验/index.md`
- Structure rules: `../../references/page/页面设计器/基础结构/index.md`
- Scenario examples: `../../references/page/页面设计器/场景示例/index.md`
- Checklist: `../../references/page/页面设计器/检查清单/index.md`
- Common errors: `../../references/page/页面设计器/常见错误/index.md`
- Core Schema spec: `../../references/page/设计器 Schema 规范定义/index.md`
- Normalize/validate detail: `../../references/page/设计器 Schema 规范定义/08-规范化与校验.md`
- List scenario: `../../references/page/页面设计器/场景示例/列表示例.md`
- Form/detail/workflow form scenario: `../../references/page/页面设计器/场景示例/表单示例.md`
- Full list schema example: `../../references/page/设计器 Schema 规范定义/列表示例.md`
- Full form schema example: `../../references/page/设计器 Schema 规范定义/表单示例.md`

## Steps

1. Read `../../references/page/页面设计器/index.md` and `../../references/page/页面设计器/生成与校验/index.md`.
2. Verify title, pagetag, device, pageType, endpoint, fields, query, and cross-asset references.
3. Keep `device=desktop` unless user explicitly requests mobile/H5/small-screen.
4. Choose scenario reference: list pages read `../../references/page/页面设计器/场景示例/列表示例.md`; form, detail, and workflow form pages read `../../references/page/页面设计器/场景示例/表单示例.md`.
5. Write/update `.lowcode-plans/<apptag>/page/<asset-id>-plan.md` with input IR summary, confirmation/source table, page structure plan, dry-run command/result, and validation command/result. Do not leave a status-only placeholder plan.
6. After approval, call `../../scripts/add_page.py`.
7. Run `../../scripts/validate_json.py <target-file>` for page designer JSON structure and model/component references.

## Page ID Rules

- Top-level `id` keeps the original stable schema id logic: derive it from `pagetag` by replacing underscores with hyphens and appending `-page`, for example `test_projectinfo_list` -> `test-projectinfo-list-page`.
- List pages do not need a top-level `pageId`; keep top-level `id` as the local schema/component id base.
- Form and detail pages that are opened by renderer URLs must include a top-level `pageId` using the designer runtime format `page_<timestamp>`, for example `page_1781580614416`.
- `pageId` is the renderer target id and must not replace top-level `id`.
- For form pages, generate or capture the real designer `pageId` first. If the value is already known from a real designer export, platform preview, or IR, pass that exact value with `add_page.py --page-id <form-page-id>`.
- If no real platform `pageId` is known, do not invent or hand-round a value. Omit `--page-id` and let `add_page.py` generate a current millisecond timestamp value.
- The generated fallback must be a real millisecond timestamp from execution time, not a placeholder, rounded timestamp, or manually typed value such as `page_1781760000000`.
- Use the final concrete `page_<millisecond-timestamp>` value consistently in the form page top-level `pageId` and in list add/edit/detail renderer URLs.

## Model Binding Rules

- Component model bindings use expression cells, not raw string paths.
- Generate `props.modelValue` as `{ "$expr": "$model.<modelAlias>" }` for table collection binding.
- Generate field bindings as `{ "$expr": "$model.<modelAlias>.<fieldName>" }`, for example `{ "$expr": "$model.projectinfo.projectname" }`.
- For controls with value/text pairs, generate `props.text` as the same expression-cell shape pointing at the display-text model field.
- Do not generate legacy string bindings such as `"modelValue": "projectinfo.projectname"`.

## List Page Defaults

When `pageType=list`, generate a page consistent with the standard list scenario:

- Hide the toolbar title slot by default (`showTitleSlot=false`); do not show a duplicated page title in the upper-left toolbar.
- Generate a companion form page for add/edit/detail dialogs when the list page includes add, edit, or detail actions. The list page itself only contains list/table structure and must not be used as the dialog target.
- Generate or identify the companion form page before finalizing the list URL. Read the target form JSON top-level `pageId` and use that exact value as `<form-page-id>`.
- Generate an add button with text `新增记录`, `openType=dialog`, and a renderer URL like `vuepagedesigner/renderer/add?pageId=<form-page-id>`.
- Generate a delete-selected toolbar button with text `删除选中`.
- Append a table action column as the last table column. It should contain edit, detail, and delete actions.
- Edit and detail actions open renderer pages in dialogs using `pageId=<form-page-id>`. Delete action stays on the current list and uses the standard delete confirmation tip.
- Keep list table multi-selection visible (`rowSelection=checkbox`, `showSelectionColumn=true`) when delete-selected or row actions are generated.
- When calling `add_page.py` for the list page, pass `--form-page-id <form-page-id>` where `<form-page-id>` is the companion form JSON's top-level `pageId`, not the list page id.
- Do not pass a list page `id` as `--form-page-id`, and do not convert list page `id` to `page_<timestamp>`.

## Boundaries

- Do not generate event for CRUD endpoints.
- Do not generate workflow; workflow consumes pagetag after the page asset exists or after the IR provides it.

