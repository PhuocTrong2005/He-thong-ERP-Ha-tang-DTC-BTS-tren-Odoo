"""Repair known failed BTS mail and defer retries beyond Gmail's quota window."""

from datetime import timedelta

from odoo import fields


Mail = env["mail.mail"].sudo()
Template = env["mail.template"].sudo()
Server = env["ir.mail_server"].sudo()

server = Server.search([("smtp_host", "=", "smtp.gmail.com")], limit=1)
if not server:
    raise AssertionError("No active Gmail SMTP server was found")
server.write({
    "smtp_port": 587,
    "smtp_encryption": "starttls",
})

subject_fixes = {
    "dtc_bts_contract.mail_template_signature_stage1_rejected": (
        "[DTC BTS] Thông báo từ chối ký số hồ sơ - "
        "{{ object.name }} - {{ object.project_id.display_name }}"
    ),
    "dtc_bts_contract.mail_template_signature_stage1_completed": (
        "[DTC BTS] Xác nhận hoàn tất ký số hồ sơ - "
        "{{ object.name }} - {{ object.project_id.display_name }}"
    ),
}
for xmlid, subject in subject_fixes.items():
    template = env.ref(xmlid, raise_if_not_found=False)
    if template:
        template.write({"subject": subject})

failed = Mail.search([("state", "=", "exception")])
retry_at = fields.Datetime.now() + timedelta(hours=26)
for mail in failed:
    clean_subject = " ".join((mail.subject or "").split())
    mail.write({
        "subject": clean_subject,
        "state": "outgoing",
        "failure_type": False,
        "failure_reason": False,
        "scheduled_date": retry_at,
    })

env.cr.commit()
print("FAILED_MAIL_QUEUE_REPAIRED")
print({"deferred_mails": failed.ids, "retry_at": retry_at, "smtp_port": server.smtp_port})
