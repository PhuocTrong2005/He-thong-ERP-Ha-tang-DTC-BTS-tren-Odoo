"""Create a deterministic analytics dataset for the BTS application.

Run from the repository root:

    docker cp scripts/import_analytics_demo_data.py \
        mis_odoo_web:/tmp/import_analytics_demo_data.py
    docker compose exec -T odoo sh -lc \
        'odoo shell ... < /tmp/import_analytics_demo_data.py'

All generated business codes start with ``ANL-``.  The script is idempotent:
records are searched by their stable business keys before they are created.
Do not pipe this UTF-8 file through Windows PowerShell ``Get-Content``.
"""

from datetime import date, datetime, time, timedelta

from dateutil.relativedelta import relativedelta


TODAY = date.today()
PREFIX = "ANL-"
CONTEXT = {
    "tracking_disable": True,
    "mail_notrack": True,
    "mail_create_nosubscribe": True,
    "mail_auto_subscribe_no_notify": True,
    "bts_skip_workflow_email": True,
}

PROVINCES = [
    ("Đồng Tháp", "Cao Lãnh", 10.4938, 105.6882),
    ("An Giang", "Long Xuyên", 10.3864, 105.4352),
    ("Tiền Giang", "Mỹ Tho", 10.3600, 106.3600),
    ("Bến Tre", "Bến Tre", 10.2434, 106.3758),
    ("Vĩnh Long", "Vĩnh Long", 10.2537, 105.9722),
    ("Cần Thơ", "Ninh Kiều", 10.0452, 105.7469),
    ("Trà Vinh", "Trà Vinh", 9.9347, 106.3453),
    ("Sóc Trăng", "Sóc Trăng", 9.6025, 105.9800),
]
def model(name):
    return env[name].sudo().with_context(**CONTEXT)


def find_or_create(record_model, domain, values):
    record = record_model.search(domain, limit=1)
    if record:
        return record, False
    return record_model.create(values), True


def contract_state(effective_date, expiration_date):
    if effective_date > TODAY:
        return "draft"
    days_left = (expiration_date - TODAY).days
    if days_left < 0:
        return "expired"
    if days_left < 60:
        return "renewal_agreed"
    return "active"


def month_day(month_offset, day=10):
    month_start = date(TODAY.year, TODAY.month, 1)
    target = month_start - relativedelta(months=month_offset)
    return target.replace(day=min(day, 28))


Project = model("project.project")
Station = model("project.task")
Partner = model("res.partner")
Equipment = model("maintenance.equipment")
Batch = model("bts.maintenance.batch")
Request = model("maintenance.request")
ChecklistItem = model("bts.maintenance.checklist.item")
ChecklistResult = model("bts.maintenance.checklist.result")
Proposal = model("bts.repair.proposal")
ProposalLine = model("bts.repair.proposal.line")
Contract = model("bts.contract")
Renewal = model("bts.contract.renewal")
Negotiation = model("bts.negotiation.minutes")
Handover = model("bts.station.handover")

admin_user = env.ref("base.user_admin")
project_managers = [
    env.ref(xmlid, raise_if_not_found=False)
    for xmlid in (
        "dtc_bts_base.user_dtc_ksgs_demo",
        "dtc_bts_base.user_dtc_ksgs_an_demo",
        "dtc_bts_base.user_dtc_ksgs_binh_demo",
        "dtc_bts_base.user_dtc_ksgs_cuong_demo",
        "dtc_bts_base.user_dtc_ksgs_dung_demo",
    )
]
project_managers = [user for user in project_managers if user]
if not project_managers:
    raise AssertionError(
        "No existing demo KSGS user is available"
    )
enterprise_director = env.ref(
    "dtc_bts_base.user_bts_enterprise_director_demo",
    raise_if_not_found=False,
) or admin_user
technician = env.ref(
    "dtc_bts_base.user_dtc_infrastructure_demo",
    raise_if_not_found=False,
) or admin_user
macro_category = env.ref("dtc_bts_maintenance.category_bts_macro")
cell_category = env.ref("dtc_bts_maintenance.category_bts_cell")

created = {
    "partners": 0,
    "projects": 0,
    "stations": 0,
    "equipment": 0,
    "batches": 0,
    "requests": 0,
    "checklist_results": 0,
    "failures": 0,
    "repair_proposals": 0,
    "contracts": 0,
    "renewals": 0,
    "negotiations": 0,
    "handovers": 0,
}

# Reuse master data. The import must never create users or partners.
telecom_partners = Partner.search([
    ("partner_type", "=", "telecom_partner"),
    ("active", "=", True),
], order="id")
landowners = Partner.search([
    ("partner_type", "=", "landowner"),
    ("active", "=", True),
], order="id")
if not telecom_partners:
    raise AssertionError("No existing telecom partner is available")
if not landowners:
    raise AssertionError("No existing landowner is available")

projects = []
stations_by_project = {}
station_sequence = 0

for project_index in range(1, 31):
    province, district, base_latitude, base_longitude = PROVINCES[
        (project_index - 1) % len(PROVINCES)
    ]
    station_type = "macro" if project_index % 3 else "cell"
    station_count = 5 if project_index <= 25 else 1
    telecom_partner = telecom_partners[(project_index - 1) % len(telecom_partners)]
    project_manager = project_managers[(project_index - 1) % len(project_managers)]

    if project_index <= 25:
        planned_start = TODAY - timedelta(
            days=(26 - project_index) * 55 + 180
        )
        planned_end = planned_start + timedelta(
            days=105 + (project_index % 4) * 15
        )
        acceptance_offsets = (-25, -14, -7, -3, 0, 0, 3, 8, 18, 35)
        acceptance_date = planned_end + timedelta(
            days=acceptance_offsets[(project_index - 1) % 10]
        )
        project_state = "done"
    else:
        planned_start = TODAY + timedelta(days=120 + (project_index - 26) * 30)
        planned_end = planned_start + timedelta(days=180)
        acceptance_date = False
        project_state = "draft"

    project_code = f"{PREFIX}DA-{project_index:03d}"
    project_values = {
        "name": f"Dự án BTS phân tích {province} {project_index:02d}",
        "project_code": project_code,
        "telecom_partner_id": telecom_partner.id,
        "station_type": station_type,
        "province": province,
        "district": district,
        "commune": f"Phường/Xã mẫu {((project_index - 1) % 9) + 1}",
        "planned_start_date": planned_start,
        "planned_end_date": planned_end,
        "acceptance_date": acceptance_date,
        "project_manager_id": project_manager.id,
        "enterprise_director_id": enterprise_director.id,
        "state": project_state,
    }
    project, was_created = find_or_create(
        Project,
        [("project_code", "=", project_code)],
        project_values,
    )
    if not was_created:
        project.write(project_values)
    created["projects"] += int(was_created)
    projects.append(project)

    project_stations = []
    for project_station_index in range(1, station_count + 1):
        station_sequence += 1
        station_code = f"{PREFIX}TR-{station_sequence:03d}"
        if project_state == "done":
            station_state = "operating"
            handover_state = "accepted"
            station_acceptance = acceptance_date + timedelta(
                days=project_station_index - 1
            )
        elif project_state == "in_progress":
            station_state = (
                "construction"
                if project_station_index % 2
                else "contracted"
            )
            handover_state = "not_handed"
            station_acceptance = False
        else:
            station_state = "survey"
            handover_state = "not_handed"
            station_acceptance = False

        station_values = {
            "name": f"Trạm {province} {project_index:02d}-{project_station_index:02d}",
            "station_code": station_code,
            "project_id": project.id,
            "assigned_user_id": project_manager.id,
            "user_ids": [(6, 0, [project_manager.id])],
            "station_state": station_state,
            "handover_state": handover_state,
            "acceptance_date": station_acceptance,
            "site_address": (
                f"Điểm {project_station_index}, {district}, {province}"
            ),
            "latitude": base_latitude + project_station_index * 0.008,
            "longitude": base_longitude + project_station_index * 0.009,
        }
        station, station_created = find_or_create(
            Station,
            [("station_code", "=", station_code)],
            station_values,
        )
        if not station_created:
            station.write(station_values)
        created["stations"] += int(station_created)
        project_stations.append(station)
    if project_index > 25:
        # Creating a survey-stage station synchronizes its project to survey;
        # these five seed projects must remain explicitly in draft.
        project.write({"state": "draft"})
    stations_by_project[project.id] = project_stations

# One landowner and one land contract for every station. Completed stations also
# receive an infrastructure contract linked to the land contract.
all_stations = [station for values in stations_by_project.values() for station in values]
for station_index, station in enumerate(all_stations, start=1):
    project = station.project_id
    project_number = int(project.project_code.rsplit("-", 1)[-1])
    # Draft projects intentionally stop at project + station.
    if project_number > 25:
        continue
    owner = landowners[(station_index - 1) % len(landowners)]

    infra_expiration = None
    if project_number <= 25:
        expiry_offsets = [-120, -20, 45, 75, 180, 430]
        infra_expiration = TODAY + timedelta(
            days=expiry_offsets[(station_index - 1) % len(expiry_offsets)]
        )
        # A small, intentional business-risk set feeds the dashboard warning:
        # each contract is valid on its own, but land expires before infra.
        land_expiration = (
            infra_expiration - timedelta(days=120)
            if station_index % 7 == 0
            else infra_expiration + timedelta(days=540)
        )
    else:
        land_expiration = project.planned_start_date + relativedelta(years=5)

    land_effective = project.planned_start_date - timedelta(days=45)
    land_sign = land_effective - timedelta(days=7)
    land_code = f"{PREFIX}HD-DAT-{station_index:03d}"
    land_values = {
        "contract_code": land_code,
        "contract_type": "land_lease",
        "station_id": station.id,
        "partner_id": owner.id,
        "created_by_id": project.project_manager_id.id,
        "sign_date": land_sign,
        "effective_date": land_effective,
        "expiration_date": land_expiration,
        "term_years": max(
            1,
            relativedelta(land_expiration, land_effective).years,
        ),
        "rental_price": 36_000_000 + (station_index % 8) * 6_000_000,
        "payment_cycle": "yearly",
        "alert_before_days": 30,
        "state": contract_state(land_effective, land_expiration),
        "notes": "Dữ liệu phân tích tự động ANL; ngày tháng theo timeline dự án.",
    }
    land_contract, land_created = find_or_create(
        Contract,
        [("contract_code", "=", land_code)],
        land_values,
    )
    if not land_created:
        land_contract.write(land_values)
    created["contracts"] += int(land_created)

    land_minutes = Negotiation.search([
        ("station_id", "=", station.id),
        ("memo_type", "=", "land_lease"),
    ], limit=1)
    if not land_minutes:
        Negotiation.create({
            "memo_code": f"{PREFIX}BBDP-DAT-{station_index:03d}",
            "memo_type": "land_lease",
            "station_id": station.id,
            "partner_id": owner.id,
            "memo_date": land_sign - timedelta(days=14),
            "agreed_rental_price": land_values["rental_price"],
            "discussed_terms":
                "Thống nhất vị trí, thời hạn thuê và đơn giá thuê đất.",
            "notes": "Dữ liệu vòng đời dự án ANL.",
            "state": "confirmed",
        })
        created["negotiations"] += 1

    if project_number > 25:
        continue

    infra_effective = station.acceptance_date + timedelta(days=15)
    infra_sign = infra_effective - timedelta(days=5)
    # Very old expired demo contracts must still end after they became active.
    infra_expiration = max(
        infra_expiration,
        infra_effective + timedelta(days=365),
    )
    infra_code = f"{PREFIX}HD-HT-{station_index:03d}"
    infra_values = {
        "contract_code": infra_code,
        "contract_type": "infrastructure_lease",
        "station_id": station.id,
        "partner_id": project.telecom_partner_id.id,
        "related_land_contract_id": land_contract.id,
        "created_by_id": project.project_manager_id.id,
        "sign_date": infra_sign,
        "effective_date": infra_effective,
        "expiration_date": infra_expiration,
        "term_years": max(
            1,
            relativedelta(infra_expiration, infra_effective).years,
        ),
        "rental_price": 12_000_000 + (station_index % 6) * 2_500_000,
        "payment_cycle": "monthly",
        "alert_before_days": 30,
        "state": contract_state(infra_effective, infra_expiration),
        "notes": "Dữ liệu phân tích tự động ANL.",
    }
    infra_contract, infra_created = find_or_create(
        Contract,
        [("contract_code", "=", infra_code)],
        infra_values,
    )
    if not infra_created:
        infra_contract.write(infra_values)
    created["contracts"] += int(infra_created)

    infra_minutes = Negotiation.search([
        ("station_id", "=", station.id),
        ("memo_type", "=", "infrastructure_lease"),
    ], limit=1)
    if not infra_minutes:
        Negotiation.create({
            "memo_code": f"{PREFIX}BBDP-HT-{station_index:03d}",
            "memo_type": "infrastructure_lease",
            "station_id": station.id,
            "partner_id": project.telecom_partner_id.id,
            "memo_date": station.acceptance_date + timedelta(days=3),
            "agreed_rental_price": infra_values["rental_price"],
            "discussed_terms":
                "Thống nhất điều kiện cho thuê trạm và vận hành hạ tầng.",
            "notes": "Dữ liệu vòng đời dự án ANL.",
            "state": "confirmed",
        })
        created["negotiations"] += 1

    handover = Handover.search([("station_id", "=", station.id)], limit=1)
    handover_values = {
        "handover_code": f"{PREFIX}BG-{station_index:03d}",
        "station_id": station.id,
        "handover_by_id": project.project_manager_id.id,
        "received_by_id": technician.id,
        "handover_date": station.acceptance_date,
        "checklist":
            "Hợp đồng thuê đất; biên bản nghiệm thu; hồ sơ kỹ thuật trạm.",
        "notes": "Hồ sơ bàn giao demo theo vòng đời dự án ANL.",
        "state": "handed_over",
    }
    if handover:
        handover.write(handover_values)
    else:
        Handover.create(handover_values)
        created["handovers"] += 1

# Renewal dossiers cover all important workflow states without changing the
# original contracts. Land contracts avoid cross-contract expiration coupling.
renewal_states = (
    "draft",
    "in_progress",
    "pending_signature",
    "completed",
    "rejected",
    "cancelled",
)
director = env.ref(
    "dtc_bts_contract.user_dtc_contract_director_demo",
    raise_if_not_found=False,
) or admin_user
renewal_contracts = Contract.search([
    ("contract_code", "=like", f"{PREFIX}HD-DAT-%"),
], order="contract_code", limit=24)
for renewal_index, contract in enumerate(renewal_contracts, start=1):
    renewal_code = f"{PREFIX}GH-LIFE-{renewal_index:03d}"
    renewal = Renewal.search([
        ("renewal_code", "=", renewal_code),
    ], limit=1)
    state = renewal_states[(renewal_index - 1) % len(renewal_states)]
    renewal_date = min(
        TODAY - timedelta(days=renewal_index * 3),
        contract.expiration_date - timedelta(days=90),
    )
    new_sign_date = renewal_date + timedelta(days=7)
    new_effective_date = new_sign_date + timedelta(days=1)
    new_expiration_date = new_effective_date + relativedelta(years=5)
    renewal_values = {
        "renewal_code": renewal_code,
        "contract_id": contract.id,
        "state": state,
        "renewal_date": renewal_date,
        "performed_by_id": technician.id,
        "notes": "Hồ sơ gia hạn demo theo vòng đời hợp đồng ANL.",
        "new_sign_date": (
            new_sign_date
            if state in ("pending_signature", "completed", "rejected")
            else False
        ),
        "new_effective_date": (
            new_effective_date
            if state in ("pending_signature", "completed", "rejected")
            else False
        ),
        "new_expiration_date": (
            new_expiration_date
            if state in ("pending_signature", "completed", "rejected")
            else False
        ),
        "new_rental_price": (
            contract.rental_price * 1.08
            if state in ("pending_signature", "completed", "rejected")
            else False
        ),
        "signed_by_id": director.id if state == "completed" else False,
        "signed_date": (
            datetime.combine(new_sign_date, time(hour=9))
            if state == "completed"
            else False
        ),
        "rejection_reason": (
            "Cần điều chỉnh lại điều khoản đơn giá gia hạn."
            if state == "rejected"
            else False
        ),
        "rejected_by_id": director.id if state == "rejected" else False,
        "rejected_date": (
            datetime.combine(new_sign_date, time(hour=10))
            if state == "rejected"
            else False
        ),
    }
    if renewal:
        renewal.write(renewal_values)
    else:
        Renewal.create(renewal_values)
        created["renewals"] += 1

# Maintenance is only created for accepted projects. This preserves the
# invariant: commissioning/acceptance always occurs before maintenance.
for project_index, project in enumerate(projects[:25], start=1):
    project_stations = stations_by_project[project.id]
    category = macro_category if project.station_type == "macro" else cell_category
    equipment_by_station = {}
    for station in project_stations:
        equipment = Equipment.search([("station_id", "=", station.id)], limit=1)
        if not equipment:
            equipment = Equipment.create({
                "station_id": station.id,
                "category_id": category.id,
                "technician_user_id": technician.id,
                "next_action_date": TODAY + timedelta(
                    days=90 + project_index
                ),
                "bts_state": "active",
                "active": True,
            })
            created["equipment"] += 1
        else:
            equipment.write({
                "name": f"{station.station_code} - {station.name}",
            })
        equipment_by_station[station.id] = equipment

    offsets = [
        (project_index * 2) % 12,
        ((project_index * 2) + 5) % 12,
    ]
    for batch_index, offset in enumerate(offsets, start=1):
        maintenance_date = month_day(offset, 10 + project_index % 12)
        if maintenance_date < project.acceptance_date:
            maintenance_date = project.acceptance_date + timedelta(days=30)
        batch_name = f"{PREFIX}BT-{project_index:03d}-{batch_index}"
        batch_values = {
            "name": batch_name,
            "project_id": project.id,
            "maintenance_date": maintenance_date,
            "effective_date": project.acceptance_date,
            "maintenance_cycle_months": "3",
            "technician_user_id": technician.id,
        }
        batch, batch_created = find_or_create(
            Batch,
            [("name", "=", batch_name)],
            batch_values,
        )
        if batch_created:
            created["batches"] += 1

        checklist_items = ChecklistItem.search([
            ("category_id", "=", category.id),
            ("active", "=", True),
            ("frequency_months", "in", [1, 3]),
        ], order="sequence, id")

        for station_position, station in enumerate(project_stations, start=1):
            equipment = equipment_by_station[station.id]
            request = Request.search([
                ("maintenance_batch_id", "=", batch.id),
                ("equipment_id", "=", equipment.id),
            ], limit=1)
            if not request:
                request = Request.create({
                    "name": f"{batch_name} - {station.station_code}",
                    "maintenance_batch_id": batch.id,
                    "equipment_id": equipment.id,
                    "user_id": technician.id,
                    "station_sequence": station_position,
                    "station_page_state": "done",
                    "maintenance_type": "preventive",
                    "request_date": maintenance_date,
                    "schedule_date": datetime.combine(
                        maintenance_date,
                        time(hour=8),
                    ),
                    "actual_date": maintenance_date,
                })
                created["requests"] += 1
            else:
                request.write({
                    "request_date": maintenance_date,
                    "schedule_date": datetime.combine(
                        maintenance_date,
                        time(hour=8),
                    ),
                    "actual_date": maintenance_date,
                })

            existing_item_ids = set(request.checklist_result_ids.mapped("item_id").ids)
            missing_items = checklist_items.filtered(
                lambda item: item.id not in existing_item_ids
            )
            if missing_items:
                ChecklistResult.create([
                    {
                        "request_id": request.id,
                        "item_id": item.id,
                        "result_state": "stable",
                        "measurement_value": "Đạt",
                    }
                    for item in missing_items
                ])
                created["checklist_results"] += len(missing_items)

            results = request.checklist_result_ids.sorted(
                key=lambda result: (result.item_id.sequence, result.id)
            )
            results.filtered(
                lambda result: result.result_state == "stable"
            ).write({
                "measurement_value": "Đạt",
            })
            should_fail = (
                (project_index + station_position + batch_index) % 3 == 0
                and bool(results)
            )
            if not should_fail:
                request.write({"station_page_state": "done"})
                continue

            failure_count = 2 if (
                project_index + station_position + batch_index
            ) % 6 == 0 else 1
            failure_results = ChecklistResult.browse()
            for failure_index in range(failure_count):
                result_index = (
                    project_index
                    + station_position
                    + batch_index
                    + failure_index
                ) % min(5, len(results))
                result = results[result_index]
                result.write({
                    "result_state": (
                        "need_replacement"
                        if (station_position + failure_index) % 5 == 0
                        else "need_repair"
                    ),
                    "measurement_value": "Không đạt",
                    "note": "Hư hỏng mẫu phục vụ dashboard phân tích.",
                })
                failure_results |= result
            created["failures"] += len(failure_results)
            request.write({"station_page_state": "failed"})

            proposal = Proposal.search([
                ("maintenance_request_id", "=", request.id),
            ], limit=1)
            proposal_state = (
                "done"
                if maintenance_date <= TODAY - timedelta(days=60)
                else "confirmed"
            )
            estimated_cost = sum(
                2_000_000
                if result.result_state == "need_repair"
                else 7_500_000
                for result in failure_results
            )
            if not proposal:
                proposal = Proposal.create({
                    "maintenance_request_id": request.id,
                    "proposed_by_id": technician.id,
                    "issue_summary": (
                        f"Khắc phục {len(failure_results)} hạng mục tại "
                        f"{station.station_code}"
                    ),
                    "estimated_cost": estimated_cost,
                    "priority": (
                        "high" if estimated_cost >= 7_500_000 else "normal"
                    ),
                    "state": proposal_state,
                    "repair_result": (
                        "Đã xử lý và nghiệm thu."
                        if proposal_state == "done"
                        else False
                    ),
                })
                created["repair_proposals"] += 1
            else:
                proposal.write({
                    "issue_summary": (
                        f"Khắc phục {len(failure_results)} hạng mục tại "
                        f"{station.station_code}"
                    ),
                    "repair_result": (
                        "Đã xử lý và nghiệm thu."
                        if proposal_state == "done"
                        else False
                    ),
                })

            for result in failure_results:
                line = ProposalLine.search([
                    ("proposal_id", "=", proposal.id),
                    ("checklist_result_id", "=", result.id),
                ], limit=1)
                if not line:
                    ProposalLine.create({
                        "proposal_id": proposal.id,
                        "maintenance_request_id": request.id,
                        "station_id": station.id,
                        "checklist_result_id": result.id,
                        "item_id": result.item_id.id,
                        "result_state": result.result_state,
                        "technician_note": result.note,
                        "estimated_cost": (
                            2_000_000
                            if result.result_state == "need_repair"
                            else 7_500_000
                        ),
                    })
                else:
                    line.write({
                        "technician_note": result.note,
                    })

        if batch.state not in ("done", "cancelled"):
            batch.write({"state": "done"})

# Final consistency audit. Raising aborts the entire transaction.
generated_projects = Project.search([("project_code", "=like", f"{PREFIX}DA-%")])
assert len(generated_projects) == 30, (
    f"Expected 30 generated projects, found {len(generated_projects)}"
)
for project in generated_projects:
    project_number = int(project.project_code.rsplit("-", 1)[-1])
    expected_station_count = 1 if project_number > 25 else 5
    generated_stations = project.task_ids.filtered(
        lambda station: (station.station_code or "").startswith(f"{PREFIX}TR-")
    )
    assert len(generated_stations) == expected_station_count, (
        f"{project.project_code}: expected {expected_station_count} generated "
        f"stations, found {len(generated_stations)}"
    )
    if project_number > 25:
        assert project.state == "draft"
    assert project.planned_start_date <= project.planned_end_date
    if project.acceptance_date:
        assert project.acceptance_date >= project.planned_start_date

generated_batches = Batch.search([("name", "=like", f"{PREFIX}BT-%")])
for batch in generated_batches:
    assert batch.project_id.acceptance_date
    assert batch.maintenance_date >= batch.project_id.acceptance_date
    for request in batch.request_ids:
        assert request.actual_date >= batch.project_id.acceptance_date

generated_contracts = Contract.search([
    ("contract_code", "=like", f"{PREFIX}HD-%"),
])
for contract in generated_contracts:
    assert contract.effective_date <= contract.expiration_date
    assert contract.sign_date <= contract.effective_date
    if contract.contract_type == "infrastructure_lease":
        assert contract.related_land_contract_id
        assert contract.related_land_contract_id.station_id == contract.station_id

assert Negotiation.search_count([
    ("project_id.project_code", "=like", f"{PREFIX}DA-%"),
]) >= len([station for station in all_stations if station.project_id.state != "draft"])
assert Handover.search_count([
    ("project_id.project_code", "=like", f"{PREFIX}DA-%"),
]) == len([
    station
    for station in all_stations
    if int(station.project_id.project_code.rsplit("-", 1)[-1]) <= 25
])
assert Renewal.search_count([
    ("renewal_code", "=like", f"{PREFIX}GH-%"),
]) >= len(renewal_contracts)

env.cr.commit()

summary = {
    "projects": len(generated_projects),
    "stations": Station.search_count([
        ("station_code", "=like", f"{PREFIX}TR-%"),
    ]),
    "accepted_projects": len(generated_projects.filtered("acceptance_date")),
    "equipment": Equipment.search_count([
        ("station_id.station_code", "=like", f"{PREFIX}TR-%"),
    ]),
    "maintenance_batches": len(generated_batches),
    "maintenance_requests": Request.search_count([
        ("maintenance_batch_id.name", "=like", f"{PREFIX}BT-%"),
    ]),
    "checklist_results": ChecklistResult.search_count([
        ("request_id.maintenance_batch_id.name", "=like", f"{PREFIX}BT-%"),
    ]),
    "failure_results": ChecklistResult.search_count([
        ("request_id.maintenance_batch_id.name", "=like", f"{PREFIX}BT-%"),
        ("result_state", "in", ["need_repair", "need_replacement"]),
    ]),
    "repair_proposals": Proposal.search_count([
        ("maintenance_request_id.maintenance_batch_id.name", "=like", f"{PREFIX}BT-%"),
    ]),
    "contracts": len(generated_contracts),
    "land_contracts": len(
        generated_contracts.filtered(
            lambda contract: contract.contract_type == "land_lease"
        )
    ),
    "infrastructure_contracts": len(
        generated_contracts.filtered(
            lambda contract: contract.contract_type == "infrastructure_lease"
        )
    ),
    "intentional_expiry_risks": len(
        generated_contracts.filtered(
            lambda contract: (
                contract.contract_type == "infrastructure_lease"
                and contract.related_land_contract_id.expiration_date
                < contract.expiration_date
            )
        )
    ),
}

print("ANALYTICS_DEMO_IMPORT_OK")
print("Created this run:", created)
print("Dataset totals:", summary)
