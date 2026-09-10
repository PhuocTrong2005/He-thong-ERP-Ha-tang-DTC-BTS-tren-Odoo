"""Create deterministic demo records for every cancellation review stage.

Prerequisite: run ``import_analytics_demo_data.py`` first. Run with:

    docker cp scripts/import_cancellation_workflow_demo_data.py \
        mis_odoo_web:/tmp/import_cancellation_workflow_demo_data.py

Do not pipe this UTF-8 file through Windows PowerShell ``Get-Content``.
"""

from datetime import timedelta

from odoo import fields


CONTEXT = {
    "tracking_disable": True,
    "mail_notrack": True,
    "mail_create_nosubscribe": True,
    "mail_auto_subscribe_no_notify": True,
}
today = fields.Date.context_today(env.user)
now = fields.Datetime.now()


def model(name):
    return env[name].sudo().with_context(**CONTEXT)


Project = model("project.project")
Station = model("project.task")
Minutes = model("bts.negotiation.minutes")
Contract = model("bts.contract")
Renewal = model("bts.contract.renewal")

ksgs = env.ref("dtc_bts_base.user_dtc_ksgs_demo")
infrastructure = env.ref("dtc_bts_base.user_dtc_infrastructure_demo")
enterprise_director = env.ref(
    "dtc_bts_base.user_bts_enterprise_director_demo"
)

projects = Project.search([
    ("project_code", "=like", "ANL-DA-%"),
    ("state", "!=", "cancelled"),
], order="project_code")
if len(projects) < 6:
    raise AssertionError("Cần ít nhất 6 dự án ANL chưa hủy để tạo dữ liệu workflow")

projects.write({
    "enterprise_director_id": enterprise_director.id,
})


minute_specs = [
    ("ANL-BBDP-NUT-KSGS", False, False),
    ("ANL-BBDP-CHO-GDXN", True, False),
    ("ANL-BBDP-CHO-BGD", True, True),
]
used_station_ids = []
created_minutes = Minutes
for index, (code, reported, escalated) in enumerate(minute_specs):
    minute = Minutes.search([("memo_code", "=", code)], limit=1)
    if not minute:
        minute = Minutes.search([
            ("project_id", "in", projects.ids),
            ("station_id.station_state", "!=", "cancelled"),
            ("station_id", "not in", used_station_ids),
            ("memo_type", "=", "land_lease"),
            ("decision_at", "=", False),
        ], order="project_id, station_id", limit=1)
        station = minute.station_id or Station.search([
            ("project_id", "in", projects.ids),
            ("station_state", "!=", "cancelled"),
            ("id", "not in", used_station_ids),
        ], order="project_id, station_code", limit=1)
        if not station:
            raise AssertionError("Không còn trạm phù hợp để tạo biên bản demo")
        used_station_ids.append(station.id)
    else:
        station = minute.station_id
        used_station_ids.append(station.id)
    station.project_id.write({"project_manager_id": ksgs.id})
    station.write({
        "assigned_user_id": ksgs.id,
        "user_ids": [(6, 0, [ksgs.id])],
    })
    values = {
        "memo_code": code,
        "memo_type": "land_lease",
        "station_id": station.id,
        "memo_date": today - timedelta(days=20 - index * 3),
        "state": "draft",
        "notes": "Dữ liệu demo luồng báo đàm phán thuê đất thất bại.",
        "land_negotiation_failed": reported,
        "land_negotiation_failed_reason":
            "Chủ đất không thống nhất đơn giá và thời hạn thuê."
            if reported else False,
        "land_negotiation_failed_by_id": ksgs.id if reported else False,
        "land_negotiation_failed_at":
            now - timedelta(days=3 - index) if reported else False,
        "failure_review_state":
            ("director_pending" if escalated else "enterprise_pending")
            if reported else False,
        "failure_escalated_by_id":
            enterprise_director.id if escalated else False,
        "failure_escalated_at":
            now - timedelta(days=1) if escalated else False,
        "decision_reason":
            "Đề nghị BGĐ xem xét hủy do không còn phương án vị trí."
            if escalated else False,
        "decision_type": False,
        "decision_by_id": False,
        "decision_at": False,
    }
    if minute:
        minute.write(values)
    else:
        minute = Minutes.create(values)
    created_minutes |= minute

contracts = Contract.search([
    ("project_id", "in", projects.ids),
    ("state", "in", ("active", "renewal_agreed", "expired")),
], order="expiration_date, contract_code")
if len(contracts) < 3:
    raise AssertionError("Cần ít nhất 3 hợp đồng ANL để tạo dữ liệu gia hạn")

renewal_specs = [
    ("ANL-GH-NUT-HT", False, False),
    ("ANL-GH-CHO-GDXN", True, False),
    ("ANL-GH-CHO-BGD", True, True),
]
created_renewals = Renewal
used_contract_ids = []
for index, (code, reported, escalated) in enumerate(renewal_specs):
    renewal = Renewal.search([("renewal_code", "=", code)], limit=1)
    if not renewal:
        contract = contracts.filtered(
            lambda rec: rec.id not in used_contract_ids
        )[:1]
        if not contract:
            raise AssertionError("Không còn hợp đồng phù hợp để tạo gia hạn demo")
        used_contract_ids.append(contract.id)
    else:
        contract = renewal.contract_id
        used_contract_ids.append(contract.id)
    values = {
        "renewal_code": code,
        "contract_id": contract.id,
        "renewal_date": today - timedelta(days=12 - index * 2),
        "performed_by_id": infrastructure.id,
        "notes": "Dữ liệu demo luồng báo gia hạn thất bại.",
        "non_renewal_type": (
            "land" if contract.contract_type == "land_lease" else "station"
        ) if reported else False,
        "non_renewal_reason":
            "Đối tác không thống nhất điều kiện gia hạn hợp đồng."
            if reported else False,
        "non_renewal_reported_by_id":
            infrastructure.id if reported else False,
        "non_renewal_reported_at":
            now - timedelta(days=3 - index) if reported else False,
        "non_renewal_review_state":
            ("director_pending" if escalated else "enterprise_pending")
            if reported else False,
        "non_renewal_escalated_by_id":
            enterprise_director.id if escalated else False,
        "non_renewal_escalated_at":
            now - timedelta(days=1) if escalated else False,
        "decision_reason":
            "Đề nghị BGĐ quyết định do không thể tiếp tục gia hạn."
            if escalated else False,
        "decision_type": False,
        "decision_by_id": False,
        "decision_at": False,
    }
    if renewal:
        renewal.write(values)
    else:
        renewal = Renewal.create(values)
    created_renewals |= renewal

assert Minutes.search_count([
    ("memo_code", "in", [item[0] for item in minute_specs]),
]) == 3
assert Renewal.search_count([
    ("renewal_code", "in", [item[0] for item in renewal_specs]),
]) == 3

env.cr.commit()
print("CANCELLATION_WORKFLOW_DEMO_OK")
print("Negotiation:", created_minutes.mapped("memo_code"))
print("Renewal:", created_renewals.mapped("renewal_code"))
