---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 图片上传（SformImageUpload）
sdoc-doc-id: d4a445d8-2373-46bd-b4ae-7d9bb668c750
---

# SformImageUpload 图片上传

## 组件选择摘要

- 适用场景：图片上传、头像、证照、图片材料。
- 优先使用：上传对象是图片，并需要图片预览或图片类限制。
- 不建议用于：通用附件上传。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_465cd087/sform-image-upload.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| multiple | `boolean` | `false` | 是否多选 |
| imageSize | `number` | `140` | 图片展示大小 |
| numLimit | `number \| ''` | `''` | 最大可上传图片数 |
| numLimitAlert | `string` | `''` | 上传超过最大可上传文件数的文本提示 |
| sizeLimit | `number` | `0` | 最大可上传图片大小，单位 KB |
| typeLimit | `string` | `'gif,jpg,jpeg,bmp,png,webp'` | 可上传图片后缀 |
| accept | `string` | `'image/*'` | 可接受图片类型 |
| clientTag | `string` | `''` | 业务标识 |
| enableSort | `boolean` | `false` | 是否允许拖拽图片进行排序 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| beforeUpload | `rawFile: UploadRawFile, replaceTarget?: UploadImage` | 上传前的钩子函数 |
| beforeRemove | `uploadFile: UploadImage` | 删除前的钩子函数 |
| beforeDownload | `uploadFile: UploadImage` | 下载前的钩子函数 |
| onRemove | `uploadFile: UploadImage, uploadFiles: UploadImage[]` | 删除文件时的钩子函数 |
| onChange | `uploadFile: UploadImage, uploadFiles: UploadImage[]` | 选择文件、上传成功或上传失败时的钩子函数 |
| onSuccess | `response: any, uploadFile: UploadImage, uploadFiles: UploadImage[]` | 上传成功时的钩子函数 |
| onError | `error: Error, uploadFile: UploadImage, uploadFiles: UploadImage[]` | 发生错误时的钩子函数 |
