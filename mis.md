# 格式
## 完整结构
> 生成规则：对话或 JSON 入参可以只提供关键字段，但最终落盘的 `fields[]` 必须补齐下方中文备注标出的模板属性，不能只生成 `name/type/description/length` 这类瘦字段。

```yaml
# 固定标识
type: mis
# 模型名称
name: customer_info
# 描述
description: 客户基础信息表，存储客户核心档案数据
# 表名
tableName: customer_info
# 字段列表
fields:
    # 字段名
  - name: customer_name
    # 类型(字符串型-nvarchar，整数型-Integer，双精度浮点型-Numeric，日期型-DateTime，大文本型-ntext，二进制型-Image)
    type: nvarchar
    # 描述 显示名称
    description: 客户姓名
    # 长度
    length: 50
    # 代码项绑定
    datasourceCodename:""
    # 字段显示类型(combobox-下拉列表，datagrid-表格控件，radiobuttonlist-单选按钮组，checkbox-复选框，spinner-数字微调，datepicker-日期控件，textbox-文本输入框，ouradiotree-部门单选树，ouchecktree-部门多选树，userradiotree-部门用户单选树，userchecktree-部门用户多选树，webuploader-文件上传，webeditor-ewebeidtor，textarea-多行文本输入框，dropdownradiotree-下拉单选树，dropdownchecktree-下拉多选树，fckeditor-富文本编辑器，checkboxlist-复选框组)
    fielddisplaytype: textbox
    # 是否是部门字段
    isframeou:false
    # 是否是用户字段
    isframeuser:false
    # 是否主键
    isforeignkey:false
    # 是否自增字段
    autoincrease:false
    # 是否必填字段
    mustfill:false
    # 字段默认值
    defaultvalue:""
    # 是否唯一字段   
    uniquefield:false
    # 是否非空字段
    notnull: true
    fieldjd:2
    ismillisecond:false 
    precision: 0
    frameMj:0
    controlwidth:1
    ordernumingrid:10
    dispfielddesc:false
    fielddesc:""
    todispingrid: true
    isquerycondition:false
    isorderfield:false
    orderdirection:"asc"
    isexportexcel:false
    gridmultirows:false
    gridwidth:100
    dispInadd: true	
  - name: customer_mobile
    type: nvarchar
    description: 客户手机号
    originalType: nvarchar
    fieldnumtype:2
    length: 50
    autoincrease:false
    fieldjd:2
    ismillisecond:false
    isforeignkey:false
    uniquefield:false
    defaultvalue:""
    mustfill:false
    precision: 0
    notnull: true
    frameMj:0
    fielddisplaytype: textbox
    controlwidth:1
    ordernumingrid:10
    dispfielddesc:false
    fielddesc:""
    todispingrid: true
    isquerycondition:false
    isorderfield:false
    orderdirection:"asc"
    isexportexcel:false
    gridmultirows:false
    gridwidth:100
    dispInadd: true
    datasourceCodename:""
    isframeou:false
    isframeuser:false
    iscustom:false
  - name: customer_level
    type: nvarchar
    description: 客户等级
    originalType: nvarchar
    fieldnumtype:2
    length: 50
    autoincrease:false
    fieldjd:2
    ismillisecond:false
    isforeignkey:false
    uniquefield:false
    defaultvalue:""
    mustfill:false
    precision: 0
    notnull: true
    frameMj:0
    fielddisplaytype: textbox
    controlwidth:1
    ordernumingrid:10
    dispfielddesc:false
    fielddesc:""
    todispingrid: true
    isquerycondition:false
    isorderfield:false
    orderdirection:"asc"
    isexportexcel:false
    gridmultirows:false
    gridwidth:100
    dispInadd: true
    datasourceCodename:""
    isframeou:false
    isframeuser:false
    iscustom:false
  - name: customer_status
    type: nvarchar
    description: 客户状态
    originalType: nvarchar
    fieldnumtype:2
    length: 50
    autoincrease:false
    fieldjd:2
    ismillisecond:false
    isforeignkey:false
    uniquefield:false
    defaultvalue:""
    mustfill:false
    precision: 0
    notnull: true
    frameMj:0
    fielddisplaytype: textbox
    controlwidth:1
    ordernumingrid:10
    dispfielddesc:false
    fielddesc:""
    todispingrid: true
    isquerycondition:false
    isorderfield:false
    orderdirection:"asc"
    isexportexcel:false
    gridmultirows:false
    gridwidth:100
    dispInadd: true
    datasourceCodename:""
    isframeou:false
    isframeuser:false
    iscustom:false
  - name: create_time
    type: datetime
    description: 创建时间
    originalType: datetime
    fieldnumtype:2
    length: 50
    autoincrease:false
    fieldjd:2
    ismillisecond:false
    isforeignkey:false
    uniquefield:false
    defaultvalue:""
    mustfill:false
    precision: 0
    notnull: true
    frameMj:0
    fielddisplaytype: textbox
    controlwidth:1
    ordernumingrid:10
    dispfielddesc:false
    fielddesc:""
    todispingrid: true
    isquerycondition:false
    isorderfield:false
    orderdirection:"asc"
    isexportexcel:false
    gridmultirows:false
    gridwidth:100
    dispInadd: true
    datasourceCodename:""
    isframeou:false
    isframeuser:false
    iscustom:false
  - name: customer_remark
    type: nvarchar
    description: 客户备注
    originalType: ntext
    fieldnumtype:2
    length: 50
    autoincrease:false
    fieldjd:2
    ismillisecond:false
    isforeignkey:false
    uniquefield:false
    defaultvalue:""
    mustfill:false
    precision: 0
    notnull: true
    frameMj:0
    fielddisplaytype: textbox
    controlwidth:1
    ordernumingrid:10
    dispfielddesc:false
    fielddesc:""
    todispingrid: true
    isquerycondition:false
    isorderfield:false
    orderdirection:"asc"
    isexportexcel:false
    gridmultirows:false
    gridwidth:100
    dispInadd: true
    datasourceCodename:""
    isframeou:false
    isframeuser:false
    iscustom:false
# 关联关系
relations:
    # 关联名称
  - name: link_to_customer_info
    # 目标表
    targetmodel:"customer_main"
    # 目标字段
    targetfield:"rowguid"
    # 当前字段
    currentfield:"pid"
    # 当前表
    currentmodel:"customer_info"
    # 类型（0-一对一，1-一对多）
    type: 1
```

## 引用关系结构

# 说明
对上述定义的结构做备注说明，当然能直接在结构里描述那更好。
