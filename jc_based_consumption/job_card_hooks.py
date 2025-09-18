import frappe
from frappe.utils import get_datetime


class JobCardHandler:
    def __init__(self, doc):
        self.doc = doc
        self.logger = frappe.logger("job_card_hooks", allow_site=True, file_count=10)

        # Work Order
        self.wo = frappe.get_doc("Work Order", doc.work_order)

        # Operasyon bilgisi
        self.operations = [op.operation for op in self.wo.operations]
        try:
            self.this_idx = self.operations.index(doc.operation)
            self.last_idx = len(self.operations) - 1
        except ValueError:
            frappe.throw(f"Operation {doc.operation} not found in Work Order {self.wo.name}")

        self.is_last = (self.this_idx == self.last_idx)

        # Tamamlanan qty
        self.completed_qty = sum([(tl.completed_qty or 0) for tl in doc.time_logs])
        if self.completed_qty <= 0:
            frappe.throw("Completed Quantity must be greater than zero for Stock Entry.")

        # Posting time
        self.posting_time = None
        if doc.actual_end_date:
            try:
                self.posting_time = get_datetime(doc.actual_end_date).time()
            except Exception:
                self.posting_time = None

    def create_consumption_entry(self):
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Consumption for Manufacture"
        se.work_order = None   # 🚫 Transfer zorunluluğunu engeller
        se.company = self.doc.company
        se.posting_date = self.doc.posting_date
        se.posting_time = self.posting_time
        se.for_quantity = float(self.completed_qty)
        se.manufactured_qty = float(self.completed_qty)
        se.fg_completed_qty = 0
        se.from_bom = 0

        se.custom_job_card_ref = self.doc.name

        plan_qty = float(self.doc.for_quantity or 1)
        factor = (float(self.completed_qty) / plan_qty) if plan_qty else 1.0

        for item in self.doc.items:
            consume_qty = (item.required_qty or 0) * factor
            row = se.append("items", {
                "item_code": item.item_code,
                "s_warehouse": self.doc.wip_warehouse,  # 🔑 WIP'ten tüketim (negatif olabilir)
                "qty": consume_qty,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": 1,
            })
            row.custom_job_card_item_ref = item.name
            self.logger.info(
                f"[{self.doc.name}] Consume {consume_qty} {item.uom} of {item.item_code} "
                f"(completed_qty={self.completed_qty}, plan_qty={plan_qty}, factor={factor:.3f})"
            )

        se.flags.ignore_validate = True  # 🔑 depo/transfer validation bypass
        se.insert(ignore_permissions=True)
        se.submit()
        frappe.msgprint(
            f"Consumption Entry {se.name} created for {self.completed_qty} qty in Job Card {self.doc.name}"
        )
        return se

    def create_manufacture_entry(self):
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Manufacture"
        se.work_order = self.doc.work_order
        se.company = self.doc.company
        se.posting_date = self.doc.posting_date
        se.posting_time = self.posting_time
        se.for_quantity = float(self.completed_qty)
        se.fg_completed_qty = float(self.completed_qty)

        se.from_bom = 1
        se.bom_no = self.wo.bom_no
        se.use_multi_level_bom = 0

        se.custom_job_card_ref = self.doc.name

        se.append("items", {
            "item_code": self.doc.production_item,
            "t_warehouse": self.doc.target_warehouse,
            "qty": float(self.completed_qty),
            "uom": self.wo.stock_uom,
            "stock_uom": self.wo.stock_uom,
            "conversion_factor": 1,
            "is_finished_item": 1
        })

        self.logger.info(f"[{self.doc.name}] FG {self.completed_qty} {self.wo.stock_uom} → {self.doc.target_warehouse}")

        se.insert(ignore_permissions=True)
        se.submit()
        frappe.msgprint(
            f"Manufacture Entry {se.name} created for {self.completed_qty} qty in Job Card {self.doc.name}"
        )
        return se

    def cancel_related_stock_entries(self):
        # Bu Job Card'dan oluşan tüm Stock Entry'leri bul
        stock_entries = frappe.get_all(
            "Stock Entry",
            filters={"custom_job_card_ref": self.doc.name, "docstatus": 1},  # sadece submitted kayıtlar
            pluck="name"
        )
        for se_name in stock_entries:
            se = frappe.get_doc("Stock Entry", se_name)
            se.cancel()
            self.logger.info(f"[{self.doc.name}] Cancelled Stock Entry {se_name}")
            frappe.msgprint(f"Stock Entry {se_name} cancelled (Job Card {self.doc.name})")

    def process_submit(self):
        if self.is_last:
            self.create_consumption_entry()
            self.create_manufacture_entry()
        else:
            self.create_consumption_entry()

    def process_cancel(self):
        self.cancel_related_stock_entries()


def on_submit_job_card(doc, method=None):
    # 🔑 Manufacturing Settings kontrolü
    use_jobcard_based_consumption = frappe.db.get_single_value(
        "Manufacturing Settings", "custom_job_card_based_consumption"
    )
    if not use_jobcard_based_consumption:
        return

    handler = JobCardHandler(doc)
    handler.process_submit()


def on_cancel_job_card(doc, method=None):
    use_jobcard_based_consumption = frappe.db.get_single_value(
        "Manufacturing Settings", "custom_job_card_based_consumption"
    )
    if not use_jobcard_based_consumption:
        return

    handler = JobCardHandler(doc)
    handler.process_cancel()