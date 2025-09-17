from erpnext.manufacturing.doctype.job_card.job_card import JobCard as ERPNextJobCard
import frappe

class CustomJobCard(ERPNextJobCard):
    def on_submit(self):
        # Manufacturing Settings kontrolü
        use_jobcard_based_consumption = frappe.db.get_single_value(
            "Manufacturing Settings",
            "custom_job_card_based_consumption"
        )

        if use_jobcard_based_consumption:
            # ✅ JC Based Consumption app'ine ait özel mantık
            from jc_based_consumption.job_card_hooks import on_submit_job_card
            on_submit_job_card(self)
        else:
            # ✅ Core ERPNext davranışı
            super().on_submit()
