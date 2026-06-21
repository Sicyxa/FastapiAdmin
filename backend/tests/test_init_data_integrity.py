"""验证 scripts/data/*.json 与数据库表名一致性。

核心规则（只要求 1 项）：
- JSON 文件名（去 .json）= 数据库表名（Model.__tablename__）
- 例：platform_invoice.json ↔ InvoiceModel.__tablename__ = "platform_invoice"

补充检查（每对 JSON-Model）：
- JSON 出现的字段必须存在于 Model 列中（多余字段 = ERROR）
- JSON 缺失必填无默认字段 = ERROR

违规时 fail。

用法：uv run python tests/test_init_data_integrity.py
"""

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = BACKEND_ROOT / "app" / "scripts" / "data"

# 非种子数据文件，校验脚本跳过
_EXCLUDED_JSON: set[str] = {"oss_licenses.json"}

# 运行时产生数据的表，无需种子 JSON（白名单）
# 业务说明：以下表的数据由系统运行产生，不在 initialize 时导入
_NO_SEED_TABLES: set[str] = {
    "gen_table",                # 代码生成器-业务表（用户在线创建）
    "gen_table_column",         # 代码生成器-字段表（随 gen_table 产生）
    "platform_email_log",       # 邮件发送日志（运行时累计）
    "platform_package_plugin",  # 套餐-插件关联（运行时由超管配置）
    "sys_role_depts",           # 角色-部门关联（运行时由超管配置）
    "sys_role_menus",           # 角色-菜单关联（运行时由超管配置）
    "sys_user_positions",       # 用户-岗位关联（运行时由 HR 配置）
    "task_job",                 # 定时任务（运行时由用户配置）
    "task_workflow",            # 工作流（运行时由用户配置）
}

# 已知会被 initialize.py 特殊处理的字段（树形结构 children）
# initialize.py 的 _RECURSIVE_TABLES = {"platform_menu", "sys_dept"} 会 pop children 再传给 Model
_ALLOWED_EXTRA_FIELDS: set[str] = {"children"}

sys.path.insert(0, str(BACKEND_ROOT))


# ────────────────────────────────────────────────────────────
# 1. 扫描所有 Model，自动建立"表名 → Model 类"映射
# ────────────────────────────────────────────────────────────

def _discover_table_to_model() -> dict[str, type]:
    """
    扫描 app/ 下所有 model.py，提取 *Model 类的 __tablename__

    返回: {tablename: ModelClass}
    """
    table_to_model: dict[str, type] = {}
    for model_file in sorted(BACKEND_ROOT.rglob("model.py")):
        rel = model_file.relative_to(BACKEND_ROOT)
        if "app" not in rel.parts:
            continue
        module_path = ".".join(rel.with_suffix("").parts)
        try:
            mod = importlib.import_module(module_path)
        except Exception as e:  # noqa: BLE001
            print(f"[IMPORT ERR] {module_path}: {type(e).__name__}: {e}")
            continue
        for name, obj in vars(mod).items():
            if not inspect.isclass(obj):
                continue
            if obj.__module__ != module_path:
                continue
            if not name.endswith("Model"):
                continue
            if name.startswith("_"):
                continue
            table_name = getattr(obj, "__tablename__", None)
            if not table_name:
                continue
            if table_name in table_to_model:
                # 同名表名不应存在多个 Model
                print(f"[WARN] 表名 {table_name!r} 被多个 Model 声明: {obj} 与 {table_to_model[table_name]}")
                continue
            table_to_model[table_name] = obj
    return table_to_model


# ────────────────────────────────────────────────────────────
# 2. 字段对应检查
# ────────────────────────────────────────────────────────────

def _model_columns(model: type) -> dict[str, dict[str, Any]]:
    cols: dict[str, dict[str, Any]] = {}
    for col in model.__table__.columns:
        cols[col.name] = {
            "type": col.type.__class__.__name__,
            "nullable": col.nullable,
            "default": col.default.arg if col.default else None,
            "server_default": col.server_default.arg if col.server_default else None,
            "primary_key": col.primary_key,
        }
    return cols


def _check_field_compat(json_path: Path, model: type) -> dict:
    """检查 JSON 字段 vs Model 列的兼容性"""
    cols = _model_columns(model)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        records = [data]
    else:
        records = data

    extra_fields: set[str] = set()
    missing_required: set[str] = set()
    type_mismatches: list[str] = []
    sample = records[0] if records else {}

    for k in sample.keys():
        if k not in cols and k not in _ALLOWED_EXTRA_FIELDS:
            extra_fields.add(k)

    for col_name, info in cols.items():
        if info["primary_key"]:
            continue
        if info["nullable"] or info["default"] is not None or info["server_default"] is not None:
            continue
        for rec in records:
            if col_name not in rec:
                missing_required.add(col_name)
                break

    type_map = {
        "INTEGER": int,
        "BIGINTEGER": int,
        "SMALLINTEGER": int,
        "VARCHAR": str,
        "String": str,
        "TEXT": str,
        "JSON": (dict, list),
        "BOOLEAN": bool,
        "DATETIME": str,
        "DATE": str,
        "TIME": str,
        "FLOAT": (int, float),
        "NUMERIC": (int, float),
    }
    for col_name, info in cols.items():
        py_type = type_map.get(info["type"])
        if py_type is None:
            continue
        for rec in records[:5]:
            v = rec.get(col_name)
            if v is None:
                continue
            if not isinstance(v, py_type):
                type_mismatches.append(f"{col_name}({info['type']}): 实际 {type(v).__name__}={v!r}")
                break

    return {
        "json_count": len(records),
        "extra_in_json": sorted(extra_fields),
        "missing_required": sorted(missing_required),
        "type_mismatches": type_mismatches,
        "ok": not extra_fields and not missing_required and not type_mismatches,
    }


# ────────────────────────────────────────────────────────────
# 3. 主流程：表名对应 + 字段对应
# ────────────────────────────────────────────────────────────

def main() -> int:
    table_to_model = _discover_table_to_model()
    print(f"扫描到 {len(table_to_model)} 个 Model 表\n")

    # 收集所有 JSON 文件
    json_files = sorted(p for p in SCRIPT_DIR.glob("*.json") if p.name not in _EXCLUDED_JSON)
    json_table_names = {p.stem for p in json_files}
    model_table_names = set(table_to_model.keys())

    # 规则 1: JSON 文件名（去 .json）必须 = Model.__tablename__
    orphan_jsons = json_table_names - model_table_names
    orphan_tables = model_table_names - json_table_names

    # 规则 2: 字段对应
    print("─" * 70)
    print("【规则 1】JSON 文件名 ↔ 数据库表名对应")
    print("─" * 70)
    bad = 0
    if orphan_jsons:
        print("✗ 下列 JSON 文件找不到对应 Model 表:")
        for name in sorted(orphan_jsons):
            print(f"    - {name}.json")
        bad += len(orphan_jsons)
    if orphan_tables:
        # 过滤掉白名单内的"运行时产生数据"表
        real_orphan = orphan_tables - _NO_SEED_TABLES
        whitelisted = orphan_tables & _NO_SEED_TABLES
        if real_orphan:
            print("✗ 下列 Model 表没有对应 JSON 种子数据（initialize 时会被跳过）:")
            for name in sorted(real_orphan):
                print(f"    - {name} ({table_to_model[name].__name__})")
            bad += len(real_orphan)
        if whitelisted:
            print(f"  ⊙ 跳过白名单表（运行时产生数据）: {len(whitelisted)} 个")
            for name in sorted(whitelisted):
                print(f"      - {name}")
    if not orphan_jsons and not orphan_tables:
        print(f"✓ 全部 {len(json_table_names)} 个 JSON 都对应了 Model 表")

    print()
    print("─" * 70)
    print("【规则 2】JSON 字段 ↔ Model 列兼容性")
    print("─" * 70)

    field_bad = 0
    for json_path in json_files:
        table_name = json_path.stem
        if table_name not in table_to_model:
            continue  # 上面已报
        model = table_to_model[table_name]
        r = _check_field_compat(json_path, model)
        mark = "✓" if r["ok"] else "✗"
        print(f"  {mark} {json_path.name} ({r['json_count']} 条) ↔ {model.__name__}")
        if r["extra_in_json"]:
            print(f"      JSON 多余字段: {r['extra_in_json']}")
        if r["missing_required"]:
            print(f"      缺失必填字段: {r['missing_required']}")
        for t in r["type_mismatches"]:
            print(f"      类型不匹配: {t}")
        if not r["ok"]:
            field_bad += 1

    print()
    total_bad = bad + field_bad
    if total_bad:
        print(f"=== 失败：表名不符 {bad} 个 + 字段不符 {field_bad} 个 ===")
        return 1
    print(f"=== 全部通过：{len(json_table_names)} 个 JSON ↔ {len(model_table_names)} 个 Model 表 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
