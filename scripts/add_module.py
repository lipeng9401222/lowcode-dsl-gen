#!/usr/bin/env python3
"""add_module.py — 创建模块 yml（含可选子模块）.

用法：
    # 创建无子模块的模块
    python add_module.py \\
        --app-root /path/to/.../<apptag> \\
        --name "主体管理" \\
        --code 9544

    # 创建含子模块的模块
    python add_module.py \\
        --app-root /path/to/.../<apptag> \\
        --name "采购立项管理" \\
        --code 9544 \\
        --sub-modules "采购人管理:9544_0001:/epoint/purchaseproject/purchase_user_list,供应商管理:9544_0002:/epoint/purchaseproject/supplier_list"

兼容：--metadata 旧参数仍可用，等价于 --app-root（输出 deprecation warn）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    assert_no_metadata_layer,
    gen_uuid,
    load_template,
    now_str,
    print_err,
    print_info,
    print_ok,
    print_warn,
    render_template,
    safe_filename,
    yaml_dump,
    yaml_load,
)


def parse_sub_modules(sub_str: str) -> list[dict]:
    """解析子模块字符串：'name:code:url,name2:code2:url2' """
    result = []
    for part in sub_str.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) < 2:
            raise ValueError(f"子模块格式错误: {part}（应为 name:code 或 name:code:url）")
        sub = {
            "name": fields[0].strip(),
            "code": fields[1].strip(),
        }
        if len(fields) >= 3 and fields[2].strip():
            sub["url"] = fields[2].strip()
        result.append(sub)
    return result


def build_sub_module(sub: dict, parent_guid: str, order: int) -> dict:
    """构造一个子模块对象."""
    guid = gen_uuid()
    url = sub.get("url", "")
    return {
        "code": sub["code"],
        "name": sub["name"],
        "guid": guid,
        "menuName": "",
        "url": url,
        "orderNumber": order,
        "isDisable": 0,
        "isBlank": 0,
        "bigIconAddress": "",
        "smallIconAddress": "",
        "moduleType": "",
        "isAddOu": 0,
        "parentGuid": parent_guid,
        "isFromSoa": 0,
        "isUse": 1,
        "i18nKey": "",
        "isReserved": 0,
        "whitelist": "",
        "tenantGuid": "",
        "moduleSource": "",
        "isSwitchApp": 0,
        "showInHomepage": "",
        "moduleSystem": "",
        "newBigIconAddress": "",
        "isKeepAlive": 0,
        "isOnlyInRoute": 0,
        "routePath": url,
        "routePathName": url.rsplit("/", 1)[-1] if url else "",
        "isVue": 1,
        "isOpenToTenant": "",
        "description": "",
        "applicationGuid": "",
        "applicationAppGuid": "",
        "createTime": now_str(),
        "updateTime": now_str(),
        "useDescription": "",
        "referenceModuleGuid": "",
        "importance": 0,
        "isTopMenu": 0,
        "isQuickCreate": 0,
        "iconType": "",
        "shortPath": "",
        "auth": {
            "moduleGuid": guid,
            "allowTo": "",
            "allowType": "",
            "isFromOa": 0,
            "isFromSoa": 0,
            "rightType": "",
            "moduleRightMode": "",
            "tenantGuid": "",
        },
    }


def cli():
    parser = argparse.ArgumentParser(description="创建模块 yml")
    parser.add_argument("--app-root", "--metadata", dest="app_root", required=True,
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名")
    parser.add_argument("--name", required=True, help="模块名称（中文）")
    parser.add_argument("--code", required=True, help="模块编码（4-8 位字符串）")
    parser.add_argument("--url", default="", help="模块 URL [空]")
    parser.add_argument(
        "--sub-modules",
        help="子模块列表，格式 name:code:url 用逗号分隔",
    )
    parser.add_argument(
        "--sub-modules-json",
        help="子模块 JSON 数组（完整字段）",
    )
    parser.add_argument(
        "--filename", help="自定义文件名（不含扩展名），默认用 name",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir():
        print_err(f"应用根目录不存在: {app_root}")
        return 1
    ok, msg = assert_no_metadata_layer(app_root)
    if not ok:
        print_err(msg)
        return 1

    module_dir = app_root / "module"
    module_dir.mkdir(parents=True, exist_ok=True)

    base_name = args.filename or safe_filename(args.name)
    target = module_dir / f"{base_name}.module.yml"

    if target.exists() and not args.force:
        print_err(f"文件已存在: {target}（--force 覆盖）")
        return 1

    # 渲染根模块
    root_guid = gen_uuid()
    template = load_template("module.yml")
    rendered = render_template(template, {
        "CODE": args.code,
        "NAME": args.name,
        "GUID": root_guid,
        "CREATE_TIME": now_str(),
        "UPDATE_TIME": now_str(),
    })

    # 写入根模块
    target.write_text(rendered, encoding="utf-8")

    # 如果有子模块，重新加载并追加
    sub_modules = []
    if args.sub_modules_json:
        try:
            sub_modules = json.loads(args.sub_modules_json)
        except json.JSONDecodeError as e:
            print_err(f"--sub-modules-json 解析失败: {e}")
            return 1
    elif args.sub_modules:
        sub_modules = parse_sub_modules(args.sub_modules)

    if sub_modules or args.url:
        try:
            data = yaml_load(target)
        except Exception as e:
            print_err(f"重新加载 yml 失败: {e}")
            return 1
        if sub_modules:
            items = []
            for i, sub in enumerate(sub_modules, start=1):
                items.append(build_sub_module(sub, root_guid, order=i * 10))
            data["items"] = items
        # 修复 url 字段（用户提供）
        if args.url:
            data["url"] = args.url
            data["routePath"] = args.url
            data["routePathName"] = args.url.rsplit("/", 1)[-1] if args.url else ""
        yaml_dump(data, target)

    print_ok(f"模块已创建: {target}")
    print_info(f"  - 名称: {args.name} (code={args.code})")
    print_info(f"  - 子模块数: {len(sub_modules)}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
