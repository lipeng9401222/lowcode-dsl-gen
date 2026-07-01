---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 上传控件（SformFileUpload）
sdoc-doc-id: c02e58a4-8140-4806-96ee-56c41fa4cf9f
---

# SformFileUpload 上传控件

## 组件选择摘要

- 适用场景：附件、文档、压缩包等通用文件上传。
- 优先使用：上传内容不限于图片，或需要附件列表。
- 不建议用于：纯图片上传或图片预览管理，应使用 SformImageUpload。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782267505437_c8617677/sform-file-upload.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| pickerText | `string` | `'选择文件'` | 按钮文本 |
| multiple | `boolean` | `false` | 是否多选 |
| numLimit | `number \| ''` | `''` | 最大可上传文件数 |
| sizeLimit | `number` | `0` | 最大可上传文件大小，单位 KB |
| typeLimit | `string` | `''` | 可上传文件后缀 |
| accept | `string` | `''` | 可接受文件类型 |
| clientTag | `string` | `''` | 业务标识 |
| enableSort | `boolean` | `false` | 是否允许排序 |
| drag | `boolean` | `false` | 是否开启拖拽上传功能 |
| showFileList | `boolean` | `true` | 是否显示已上传文件列表 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| beforeUpload | `rawFile: UploadRawFile` | 上传前的钩子函数 |
| beforeRemove | `uploadFile: UploadFile, uploadFiles: UploadFiles` | 删除前的钩子函数 |
| onRemove | `uploadFile: UploadFile, uploadFiles: UploadFiles` | 删除文件时的钩子函数 |
| onChange | `uploadFile: UploadFile, uploadFiles: UploadFiles` | 选择文件、上传成功或上传失败时的钩子函数 |
| onSuccess | `response: any, uploadFile: UploadFile, uploadFiles: UploadFiles` | 上传成功时的钩子函数 |
| onError | `error: Error, uploadFile: UploadFile, uploadFiles: UploadFiles` | 发生错误时的钩子函数 |
