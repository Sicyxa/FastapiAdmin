"""开发辅助脚本：为 platform_invoice.json 中所有已开票（status=1）的种子发票生成示例 PDF。

使用场景：
- 首次启动开发环境后，初始化数据已导入，但 PDF 文件并不存在
- 前端访问 /static/invoice/...pdf 会 404
- 跑此脚本批量生成，发票 PDF + 授权函 PDF，路径与 JSON 中 pdf_url / oss_license_pdf_url 完全一致

用法：
    cd backend
    uv run python tests/scripts/seed_invoice_pdfs.py

依赖：
- weasyprint（pyproject.toml 已包含）
- macOS 上需先安装系统库：brew install glib pango libffi（Linux 部署环境正常）
"""

import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.api.v1.module_platform.invoice.pdf_helper import (  # noqa: E402
    _render_invoice_pdf,
    _render_oss_license_pdf,
)
from app.api.v1.module_platform.invoice.schema import InvoiceOutSchema  # noqa: E402

SEED_JSON = BACKEND_DIR / "app" / "scripts" / "data" / "platform_invoice.json"


def _to_out_schema(record: dict) -> InvoiceOutSchema:
    """把 JSON 字典转为 InvoiceOutSchema，缺失的字段用合理默认填充"""
    return InvoiceOutSchema(
        id=record.get("id", 0),
        invoice_no=record["invoice_no"],
        order_id=record["order_id"],
        tenant_id=record["tenant_id"],
        invoice_type=record["invoice_type"],
        title=record["title"],
        tax_no=record.get("tax_no"),
        bank_info=record.get("bank_info"),
        address_info=record.get("address_info"),
        amount=record["amount"],
        tax_amount=record.get("tax_amount", 0),
        status=record.get("status", 1),
        description=record.get("description"),
        created_time=record.get("created_time", "2026-01-01 00:00:00"),
        updated_time=record.get("updated_time", "2026-01-01 00:00:00"),
        created_by=record.get("created_by", {"id": 1, "name": "admin"}),
        updated_by=record.get("updated_by", {"id": 1, "name": "admin"}),
    )


async def main() -> int:
    if not SEED_JSON.exists():
        print(f"[ERR] 找不到种子数据: {SEED_JSON}")
        return 1

    records = json.loads(SEED_JSON.read_text(encoding="utf-8"))
    issued = [r for r in records if r.get("status") == 1]
    print(f"种子数据共 {len(records)} 条，其中 status=1（已开票）{len(issued)} 条\n")

    if not issued:
        print("无需生成")
        return 0

    success = 0
    failed = 0
    for rec in issued:
        invoice_no = rec["invoice_no"]
        try:
            invoice = _to_out_schema(rec)
            invoice_url = _render_invoice_pdf(invoice)
            license_url = _render_oss_license_pdf(invoice)
            inv_full = BACKEND_DIR / invoice_url.lstrip("/")
            lic_full = BACKEND_DIR / license_url.lstrip("/")
            print(f"  ✓ {invoice_no}")
            print(f"      发票 PDF:   {invoice_url}  ({inv_full.stat().st_size} bytes)")
            print(f"      授权函 PDF: {license_url}  ({lic_full.stat().st_size} bytes)")
            success += 1
        except Exception as e:
            print(f"  ✗ {invoice_no}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n=== 完成：成功 {success} 条，失败 {failed} 条 ===")
    if failed:
        print("\n如果提示缺少 libgobject/pango：")
        print("  macOS:  brew install glib pango libffi")
        print("  Ubuntu: sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
