#!/usr/bin/env python3
"""field_schema.py — 低代码 yml 各节点「字段白名单」单一事实源（spec v2）.

为什么存在：
    不同模型手写 yml 时最常见的幻觉是**凭空造字段名**（例如把 workflowContext 的
    `fieldguid/fieldname/note` 写成 `contextguid/contextname/contexttext`），而这类
    捏造名既不是驼峰别名（DEPRECATED_CAMEL 抓不到），也能凑巧通过老校验（0 error 假通过）。

本文件把每个节点的**精确字段集**沉淀成机器可读的注册表，供：
    1. scripts/validate_yml.py  导入做「字段白名单 + 必填 + 捏造名→正确名」强校验；
    2. references/workflow/工作流/基础骨架/ 作为人类可读字段说明来源（lint_skill.py 守护生成侧不漂移）。

字段来源：references/workflow/工作流/基础骨架/*、assets/templates/workflow.yml、
          scripts/add_workflow.py 的产物。

schema 结构：
    {
        "required": [...],   # 必填字段（按「键是否出现」校验，不强制非空，避免与脚本默认空串冲突）
        "optional": [...],   # 合法可选字段
        "aliases":  {        # 已知错误名 → 正确名；值为 None 表示「该字段不属于本节点，应删除」
            "contextguid": "fieldguid",
            "ordernum": None,
        },
    }

严重级约定（由 validate_yml.py 落地）：
    - 命中 aliases               → error（确定性错误）
    - 缺 required                → error
    - 出现未知字段（非驼峰）      → warn，--strict 升 error
"""
from __future__ import annotations

import re

# 工作流 [#=xxx#] 运行时内置占位符：这些不需要在 workflowContext.fieldname 中定义。
# 其余形如 [#=leave_days#] 的 ascii 标识必须能在 workflowContext.fieldname 找到。
WORKFLOW_BUILTIN_PLACEHOLDERS = {
    "FirstMaterialUrl",
    "PreviousStepActivity",
    "AllBeforeActivity",
    "ExecutionContext",
    "CurrentActivity",
    "CurrentUser",
    "CurrentUserGuid",
    "CurrentOuGuid",
    "ProcessInstanceGuid",
    "ActivityInstanceGuid",
}

# [#=xxx#] 提取
PLACEHOLDER_RE = re.compile(r"\[#=\s*([^#\]]+?)\s*#\]")
# 合法相关数据参数名（ascii 标识符）；中文占位符（如 [#=申请人#]）天然不匹配，自动跳过
CONTEXT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ============================================================
# 工作流 9 类节点字段 schema
# ============================================================
WORKFLOW_NODE_SCHEMAS: dict[str, dict] = {
    # 3.1 流程基本信息
    "workflowProcess": {
        "required": ["processguid", "processname", "designversion", "status", "tag"],
        "optional": [
            "note", "isvue", "ordernum",
            "isnewversion", "customtype", "cansimpledisplay", "statemachinetag",
            "appguid", "baseouguid", "tenantguid",
        ],
        "aliases": {},
    },
    # 3.2.1 活动节点
    "activity": {
        "required": [
            "activityguid", "activityname", "activitydispname",
            "processversionguid", "activitytype", "vmlid",
        ],
        "optional": [
            "splittype", "jointype", "multitransactormode", "handleurl",
            "mobilehandleurl", "isallowaddattachfile", "timelimitenable",
            "timelimit", "timelimitunit", "earlywarning_enable", "earlywarning_time",
            "earlywarning_timeunit", "is_passwhennotransactor", "is_lockwhenmultitransactor",
            "mobilehandletype", "handletype", "iconx", "icony", "note", "nopasshandlevalue",
            "workflowActivityOperation", "workflowActivityMaterial",
            # spec v2 节点扩展字段
            "overtimeremindcontent", "smscontent", "locktimewhenmultitransactor",
            "mobileappletrules", "addattachfilesource", "joinmethodguid",
            "joinmethod", "joinmethodguid", "passrate", "passratecalculatemode",
            # 子流程节点
            "callsubprocessguid", "subprocesssynctype", "subpromultitransctormode",
        ],
        "aliases": {
            "activityName": "activityname",
            "activityType": "activitytype",
            "activityGuid": "activityguid",
        },
    },
    # 3.2.1 活动按钮
    "workflowActivityOperation": {
        "required": [
            "operationguid", "activityguid", "processversionguid",
            "operationname", "operationtype",
        ],
        "optional": [
            "is_requireopinion", "is_checkmaterialsubmit", "is_showoperationpage",
            "operationvisiablecase", "is_shownextactivity", "is_showopiniontemplete",
            "ordernumber", "statelevel", "backtargetscope", "targetactivity",
            "multitransctormode", "controlvisiablemethodguid", "defaultopinion",
            "operationpageurl", "is_showopiniontemplete",
            "targetactivitytransactorsource", "selecttransctormethodguid",
        ],
        "aliases": {
            "operationName": "operationname",
            "operationType": "operationtype",
            "operationGuid": "operationguid",
            "orderNumber": "ordernumber",
            "stateLevel": "statelevel",
            "targetActivityTransactorSource": "targetactivitytransactorsource",
            "selectTransctorMethodGuid": "selecttransctormethodguid",
        },
    },
    # 3.2.1 活动表单权限
    "workflowActivityMaterial": {
        "required": [
            "activitymaterialguid", "processversionguid", "activityguid",
            "materialguid", "accessright", "is_mustsubmit", "submittype",
        ],
        "optional": [
            "configdata", "controlvisiablemethodguid",
            "workflowActivityFieldAccess",
        ],
        "aliases": {
            "activityMaterialGuid": "activitymaterialguid",
            "accessRight": "accessright",
            "isMustSubmit": "is_mustsubmit",
            "submitType": "submittype",
            "controlVisiableMethodGuid": "controlvisiablemethodguid",
        },
    },
    "workflowActivityFieldAccess": {
        "required": [
            "rowguid", "activitymaterialguid", "processversionguid",
            "activityguid", "materialguid", "sqltablename", "fieldname",
            "fieldchinesename", "accessright", "accesstype",
        ],
        "optional": ["isallowattachwrite"],
        "aliases": {
            "rowGuid": "rowguid",
            "activityMaterialGuid": "activitymaterialguid",
            "sqlTableName": "sqltablename",
            "fieldName": "fieldname",
            "fieldChineseName": "fieldchinesename",
            "accessRight": "accessright",
            "accessType": "accesstype",
            "isAllowAttachWrite": "isallowattachwrite",
        },
    },
    # 3.2.2 退回配置
    "workflowConfig": {
        "required": ["rowguid", "processversionguid", "belongto", "configname", "configvalue", "sourceguid"],
        "optional": [],
        "aliases": {
            "rowGuid": "rowguid",
            "sourceGuid": "sourceguid",
            "configGuid": "rowguid",
            "configName": "configname",
            "configValue": "configvalue",
        },
    },
    # 3.2.3 外部方法
    "method": {
        "required": ["methodguid", "processversionguid", "typename", "methodname", "returnvaluetype"],
        "optional": ["dllpath", "note", "ordernum", "ruleguid", "tenantguid"],
        "aliases": {
            "methodGuid": "methodguid",
            "typeName": "typename",
            "methodName": "methodname",
            "returnValueType": "returnvaluetype",
            "dllPath": "dllpath",
            "ruleGuid": "ruleguid",
            "workflowMethodParameter": None,
            "params": None,
        },
    },
    # 3.2.4 事件配置
    "workflowEvent": {
        "required": ["eventguid", "eventname", "belongto", "eventtype", "processversionguid"],
        "optional": ["eventmethodguid", "ruleguid", "sourceguid", "synctype", "baseouguid", "ordernumber"],
        "aliases": {
            "eventGuid": "eventguid",
            "eventName": "eventname",
            "eventType": "eventtype",
            "eventMethodGuid": "eventmethodguid",
            "ruleGuid": "ruleguid",
            "baseOuGuid": "baseouguid",
        },
    },
    # 3.2.5 流程版本材料
    "workflowPvMaterial": {
        "required": [
            "materialguid", "processversionguid", "materialname",
            "type", "status", "submittype",
            "pageurl_read", "pageurl_readandwrite",
            "mobilepageurl_read", "mobilepageurl_readandwrite",
        ],
        "optional": [],
        "aliases": {
            "materialGuid": "materialguid",
            "materialName": "materialname",
            "materialtype": None,
            "url": None,
            "formId": None,
            "formid": None,
        },
    },
    # 3.2.6 表单数据表映射
    "workflowPvMisTableSet": {
        "required": ["mistablesetguid", "processversionguid", "materialguid", "tableguid", "sql_tablename"],
        "optional": [],
        "aliases": {
            "mistablesetGuid": "mistablesetguid",
            "materialGuid": "materialguid",
            "sqlTableName": "sql_tablename",
            "sqltablename": "sql_tablename",
            "rowguid": "mistablesetguid",
            "rowGuid": "mistablesetguid",
            "formid": None,
            "formId": None,
            "tableid": None,        # spec v2 已废弃，引擎按 sql_tablename 自动绑定
            "tableId": None,
        },
    },
    # 3.2.7 相关数据 —— 本次幻觉重灾区
    "workflowContext": {
        "required": ["fieldguid", "fieldname", "belongto", "fieldtype", "valuesource", "processversionguid", "note"],
        "optional": ["frommaterialguid", "fromsqltablename", "fromfieldname", "fieldvalue"],
        "aliases": {
            # —— 实测幻觉名（来自 contextguid 系列）——
            "contextguid": "fieldguid",
            "contextName": "fieldname",
            "contextname": "fieldname",
            "contexttext": "note",
            "contextText": "note",
            "contextvalue": "fieldvalue",
            "contextValue": "fieldvalue",
            "contexttype": "fieldtype",
            "contextType": "fieldtype",
            # —— 驼峰别名 ——
            "fieldGuid": "fieldguid",
            "fieldName": "fieldname",
            "fieldType": "fieldtype",
            "fieldValue": "fieldvalue",
            "valueSource": "valuesource",
            "fromMaterialGuid": "frommaterialguid",
            "fromSqlTableName": "fromsqltablename",
            "fromFieldName": "fromfieldname",
            # —— 已废弃 / 不属于本节点 ——
            "fromMisTableId": "fromsqltablename",
            "fromFieldId": "fromfieldname",
            "ordernum": None,       # workflowContext 没有 ordernum 字段
            "orderNum": None,
        },
    },
    # 3.2.8 流转关系
    "transition": {
        "required": ["transitionguid", "processversionguid", "fromactivityguid", "toactivityguid", "transitionname", "vmlid"],
        "optional": [
            "transitiondispname", "is_sendtomessagecenter", "priority", "type",
            "targetactivitytransactorsource", "is_targettransactor_editable",
            "is_default", "is_showasoperationbutton",
            "selecttransctormethodguid", "transactorallowmaxcount",
            "workflowTransitionCondition",
        ],
        "aliases": {
            "transitionGuid": "transitionguid",
            "fromActivityGuid": "fromactivityguid",
            "toActivityGuid": "toactivityguid",
            "transitionName": "transitionname",
            "isDefault": "is_default",
            "isTargetTransactorEditable": "is_targettransactor_editable",
            "isShowAsOperationButton": "is_showasoperationbutton",
            "isSendToMessageCenter": "is_sendtomessagecenter",
            "targetActivityTransactorSource": "targetactivitytransactorsource",
        },
    },
    # 3.2.8 流转条件
    "workflowTransitionCondition": {
        "required": ["conditionguid", "conditionname", "transitionguid", "conditionexpressiontype", "processversionguid"],
        "optional": [
            "leftvalue", "lefttext", "compareoperation", "rightvalue", "righttext",
            "valuetype", "conditionexpression", "methodguid", "ruleguid", "ordernum", "remark",
        ],
        "aliases": {
            "conditionGuid": "conditionguid",
            "conditionName": "conditionname",
            "transitionGuid": "transitionguid",
            "conditionExpressionType": "conditionexpressiontype",
            "leftValue": "leftvalue",
            "rightValue": "rightvalue",
            "valueType": "valuetype",
            "ruleGuid": "ruleguid",
        },
    },
    # 3.2.9 流程版本详情
    "workflowProcessVersion": {
        "required": [
            "processversionguid", "processguid", "processversionname",
            "version", "status", "designversion", "direction",
            "createdate", "updatedate", "author",
            "isshowlinegraph", "isshownodesimple",
            "revokeoption", "noparticipatoroption",
        ],
        "optional": [
            "revokeallowday", "revokeremindoption", "defaultuserguid",
        ],
        "aliases": {
            "processVersionGuid": "processversionguid",
            "processGuid": "processguid",
            "processVersionName": "processversionname",
            "versionnum": "version",
            "versionnumber": "version",
            "versionNum": "version",
            "versionNumber": "version",
            "isactive": None,
            "isActive": None,
            "isShowLineGraph": "isshowlinegraph",
            "isShowNodeSimple": "isshownodesimple",
            "revokeOption": "revokeoption",
            "revokeAllowDay": "revokeallowday",
            "revokeRemindOption": "revokeremindoption",
            "noParticipatorOption": "noparticipatoroption",
            "defaultUserGuid": "defaultuserguid",
        },
    },
}


# ============================================================
# 其它资产节点字段 schema（Phase 5 全技能推广）
# ============================================================
ASSET_NODE_SCHEMAS: dict[str, dict] = {
    # codeitem 子项
    "codeitem_item": {
        "required": ["codetext", "codevalue"],
        "optional": ["ordernum", "parentcodevalue", "remark", "enabled"],
        "aliases": {
            "codeText": "codetext",
            "codeValue": "codevalue",
            "codename": "codetext",
            "codeName": "codetext",
            "text": "codetext",
            "value": "codevalue",
        },
    },
    # mis 字段
    "mis_field": {
        "required": ["name", "type"],
        "optional": [
            "description", "length", "decimaldigits", "isnull", "isunique",
            "ispk", "defaultvalue", "fielddisplaytype", "datasourcecodename",
            "datasourceCodename", "iskeyword", "scale", "isframeou",
            "isframeuser", "isforeignkey", "autoincrease", "mustfill",
            "uniquefield", "notnull", "fieldjd", "ismillisecond",
            "precision", "frameMj", "controlwidth", "ordernumingrid",
            "dispfielddesc", "fielddesc", "todispingrid", "isquerycondition",
            "isorderfield", "orderdirection", "isexportexcel", "gridmultirows",
            "gridwidth", "dispInadd", "iscustom", "originalType",
            "fieldnumtype",
        ],
        "aliases": {
            "fieldName": "name",
            "fieldname": "name",
            "fieldType": "type",
            "fieldtype": "type",
            "desc": "description",
            "chinesename": "description",
            "len": "length",
        },
    },
    # event 动作流根 app
    "event_app": {
        "required": ["name"],
        "optional": ["mode", "sign", "code", "id", "rowguid", "remark", "version", "developerstag"],
        "aliases": {
            "appName": "name",
            "appSign": "sign",
            "appCode": "code",
        },
    },
}


def check_node_fields(label: str, node, schema: dict) -> list[tuple[str, str]]:
    """对单个节点做字段白名单 + 必填 + 别名校验。

    返回 [(severity, message)]，severity ∈ {'error', 'warn'}。
    - 命中 aliases（已知错误名）          → error
    - aliases 值为 None（不属于本节点）   → error
    - 缺 required（且无对应别名兜底）      → error
    - 未知字段（且非驼峰，驼峰交给 DEPRECATED_CAMEL）→ warn
    """
    issues: list[tuple[str, str]] = []
    if not isinstance(node, dict) or not isinstance(schema, dict):
        return issues
    required = schema.get("required", [])
    optional = schema.get("optional", [])
    aliases = schema.get("aliases", {})
    known = set(required) | set(optional) | set(aliases)

    alias_targets: set[str] = set()
    for key in node:
        if key in aliases:
            correct = aliases[key]
            if correct:
                issues.append((
                    "error",
                    f"{label} 字段 '{key}' 应为 '{correct}'（字段名疑似幻觉/驼峰别名，请改名）",
                ))
                alias_targets.add(correct)
            else:
                issues.append((
                    "error",
                    f"{label} 字段 '{key}' 不属于本节点（spec v2 无此字段），应删除",
                ))
        elif key not in known:
            # 驼峰键交给 validate_yml.py 的 DEPRECATED_CAMEL 递归检测，这里不重复报
            if any(ch.isupper() for ch in str(key)):
                continue
            issues.append((
                "warn",
                f"{label} 出现未知字段 '{key}'（不在字段白名单，请核对拼写或确认 spec 是否定义）",
            ))

    for req in required:
        if req not in node and req not in alias_targets:
            issues.append((
                "error",
                f"{label} 缺少必填字段 '{req}'",
            ))
    return issues


def extract_placeholders(value) -> list[str]:
    """从字符串里抽取 [#=xxx#] 占位符名（去空白）。非字符串返回空。"""
    if not isinstance(value, str):
        return []
    return [m.strip() for m in PLACEHOLDER_RE.findall(value)]


def is_context_reference(token: str) -> bool:
    """token 是否是「应在 workflowContext.fieldname 定义」的相关数据引用。

    True  → ascii 标识符且不是运行时内置占位符（如 leave_days / jine）
    False → 中文占位符、内置占位符（如 申请人 / AllBeforeActivity）
    """
    if not token or token in WORKFLOW_BUILTIN_PLACEHOLDERS:
        return False
    return bool(CONTEXT_NAME_RE.match(token))
