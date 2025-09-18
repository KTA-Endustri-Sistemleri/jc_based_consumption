import frappe
from frappe.utils import get_datetime

def on_submit_job_card(doc, method=None):
    # 🔑 Manufacturing Settings kontrolü
    use_jobcard_based_consumption = frappe.db.get_single_value(
        "Manufacturing Settings",
        "custom_job_card_based_consumption"
    )
    if not use_jobcard_based_consumption:
        return  # ➡️ Ayar kapalıysa core ERPNext mantığı çalışır

    logger = frappe.logger("job_card_hooks", allow_site=True, file_count=10)

    # İlgili Work Order'ı al
    wo = frappe.get_doc("Work Order", doc.work_order)

    # Operasyon sırası
    operations = [op.operation for op in wo.operations]
    try:
        this_idx = operations.index(doc.operation)
        last_idx = len(operations) - 1
    except ValueError:
        frappe.throw(f"Operation {doc.operation} not found in Work Order {wo.name}")
        return
    is_last = (this_idx == last_idx)

    # Tamamlanan qty
    completed_qty = sum([(tl.completed_qty or 0) for tl in doc.time_logs])
    if completed_qty <= 0:
        frappe.throw("Completed Quantity must be greater than zero for Stock Entry.")

    posting_time = None
    if doc.actual_end_date:
        try:
            posting_time = get_datetime(doc.actual_end_date).time()
        except Exception:
            posting_time = None

    # 🔑 Ara ve son operasyonlarda tüketim
    def create_consumption_entry():
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Consumption for Manufacture"
        se.work_order = None  # 🚫 Ara operasyonlarda Work Order set edilmez
        se.company = doc.company
        se.posting_date = doc.posting_date
        se.posting_time = posting_time
        se.for_quantity = float(completed_qty)
        se.manufactured_qty = float(completed_qty)
        se.fg_completed_qty = 0
        se.from_bom = 0

        se.custom_job_card_ref = doc.name

        plan_qty = float(doc.for_quantity or 1)
        factor = (float(completed_qty) / plan_qty) if plan_qty else 1.0

        for item in doc.items:
            consume_qty = (item.required_qty or 0) * factor
            row = se.append("items", {
                "item_code": item.item_code,
                "s_warehouse": doc.wip_warehouse,
                "qty": consume_qty,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": 1,
            })
            row.custom_job_card_item_ref = item.name
            logger.info(
                f"[{doc.name}] Consume {consume_qty} {item.uom} of {item.item_code} "
                f"(completed_qty={completed_qty}, plan_qty={plan_qty}, factor={factor:.3f})"
            )

        se.insert(ignore_permissions=True)
        se.submit()
        frappe.msgprint(f"Consumption Entry {se.name} created for {completed_qty} qty in Job Card {doc.name}")
        return se

    # 🔑 FG üretim (sadece son operasyonda)
    def create_manufacture_entry(doc, wo, completed_qty, posting_time, logger):
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Manufacture"
        se.work_order = doc.work_order
        se.company = doc.company
        se.posting_date = doc.posting_date
        se.posting_time = posting_time
        se.for_quantity = float(completed_qty)
        se.fg_completed_qty = float(completed_qty)

        se.from_bom = 1
        se.bom_no = wo.bom_no
        se.use_multi_level_bom = 0
        se.custom_job_card_ref = doc.name

        plan_qty = float(doc.for_quantity or 1)
        factor = (float(completed_qty) / plan_qty) if plan_qty else 1.0

        # 🔑 Hammadde tüketimi
        for item in doc.items:
            consume_qty = (item.required_qty or 0) * factor
            row = se.append("items", {
                "item_code": item.item_code,
                "s_warehouse": doc.wip_warehouse,
                "qty": consume_qty,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": 1,
            })
            row.custom_job_card_item_ref = item.name
            logger.info(
                f"[{doc.name}] Consume {consume_qty} {item.uom} of {item.item_code} "
                f"(completed_qty={completed_qty}, plan_qty={plan_qty}, factor={factor:.3f})"
            )

        # 🔑 FG satırı
        target_wh = doc.target_warehouse or wo.fg_warehouse
        if not target_wh:
            frappe.throw("Target Warehouse bulunamadı. Lütfen Job Card veya Work Order'da tanımlayın.")

        se.append("items", {
            "item_code": doc.production_item,
            "t_warehouse": target_wh,          # 🔑 v15 için zorunlu
            "qty": float(completed_qty),       # 🔑 fg_completed_qty ile aynı olmalı
            "uom": wo.stock_uom,
            "stock_uom": wo.stock_uom,
            "conversion_factor": 1,
            "is_finished_item": 1
        })

        logger.info(
            f"[{doc.name}] Manufacture (consume + FG) {completed_qty} {wo.stock_uom} → {target_wh}"
        )

        se.insert(ignore_permissions=True)
        se.submit()
        frappe.msgprint(f"Manufacture Entry {se.name} created with {completed_qty} qty in Job Card {doc.name}")
        return se

    # 📦 İş mantığı
    if is_last:
        create_manufacture_entry()
    else:
        create_consumption_entry()