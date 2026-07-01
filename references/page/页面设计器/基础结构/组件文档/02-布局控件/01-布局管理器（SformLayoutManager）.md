---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 布局管理器（SformLayoutManager）
sdoc-doc-id: aa79ea9c-78f2-47ed-a768-659cd8062851
---

# SformLayoutManager 布局管理器

## 组件选择摘要

- 适用场景：页面顶层布局管理和整体区域组织。
- 优先使用：生成完整页面骨架时作为外层布局管理。
- 不建议用于：单个字段或局部按钮排版。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| height | `number \| string` | `'100%'` | 高度 |
| className | `string` | `''` | 样式类名 |
| topConfig | `RegionConfig` | - | 顶部区域配置 |
| leftConfig | `RegionConfig` | - | 左侧区域配置 |
| mainConfig | `RegionConfig` | - | 主区域配置 |
| rightConfig | `RegionConfig` | - | 右侧区域配置 |
| bottomConfig | `RegionConfig` | - | 底部区域配置 |

## 事件 (Events)

无
