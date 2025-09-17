import frappe
import math

def calc_slot_qty(total_qty, vardiya, carton_size):
    """
    WO.qty → vardiya → koli adetine göre yukarı yuvarlanmış slot miktarı
    """
    raw = total_qty / vardiya / carton_size
    rounded = math.ceil(raw)        # tam koliye yuvarla
    return rounded * carton_size


def create_job_cards_with_carton(doc, method=None, vardiya=12, carton_size=24):
    """
    Work Order submit olduğunda Job Card oluşturur.
    - OP1: tüm qty (WO.qty)
    - Diğer operasyonlar: vardiya sayısına bölünmüş, koliye yuvarlanmış
    """
    total_qty = doc.qty
    logger = frappe.logger("job_card_hooks", allow_site=True, file_count=10)

    # ⚠️ TODO: vardiya sayısını sistemden al (şu an sabit: 12)
    # ⚠️ TODO: koli adedini sistemden al (şu an sabit: 24)

    for op in doc.operations:
        if op.idx == 1:  # OP1 → tek kart, tüm qty
            jc = frappe.new_doc("Job Card")
            jc.work_order = doc.name
            jc.operation = op.operation
            jc.for_quantity = total_qty
            jc.company = doc.company
            jc.posting_date = doc.expected_delivery_date or frappe.utils.nowdate()
            jc.insert(ignore_permissions=True)
            logger.info(f"[AUTO] OP1 için Job Card {jc.name} ({total_qty} qty)")
        else:
            slot_qty = calc_slot_qty(total_qty, vardiya, carton_size)
            for i in range(vardiya):
                jc = frappe.new_doc("Job Card")
                jc.work_order = doc.name
                jc.operation = op.operation
                jc.for_quantity = slot_qty
                jc.company = doc.company
                jc.posting_date = doc.expected_delivery_date or frappe.utils.nowdate()
                jc.insert(ignore_permissions=True)
                logger.info(f"[AUTO] {op.operation} için Job Card {jc.name} ({slot_qty} qty)")