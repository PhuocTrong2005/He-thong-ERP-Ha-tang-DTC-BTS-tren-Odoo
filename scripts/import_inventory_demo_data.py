"""Import warehouse data corresponding to the deterministic ANL-* dataset.

Prerequisite: run ``scripts/import_analytics_demo_data.py`` first.
Copy this UTF-8 file into the container and execute it there; do not pipe it
through Windows PowerShell ``Get-Content``.

The script reuses products and suppliers, then creates material requests, purchase orders,
receipts and deliveries through Odoo's stock workflow. Stable ANL-* business
keys make it safe to run repeatedly without duplicating documents.
"""

from datetime import date, datetime, time, timedelta


TODAY = date.today()
PREFIX = "ANL-"
CONTEXT = {
    "tracking_disable": True,
    "mail_notrack": True,
    "mail_create_nosubscribe": True,
    "mail_auto_subscribe_no_notify": True,
    "bts_skip_workflow_email": True,
}


def model(name):
    return env[name].sudo().with_context(**CONTEXT)


def at_noon(value):
    return datetime.combine(value, time(hour=12))


def safe_business_date(value):
    return min(value, TODAY)


def find_or_create(record_model, domain, values):
    record = record_model.search(domain, limit=1)
    if record:
        return record, False
    return record_model.create(values), True


Project = model("project.project")
Partner = model("res.partner")
MaterialRequest = model("bts.material.request")
MaterialRequestLine = model("bts.material.request.line")
RepairProposal = model("bts.repair.proposal")
ProposalMaterialLine = model("bts.repair.proposal.material.line")
PurchaseOrder = model("purchase.order")
Picking = model("stock.picking")
Warehouse = model("stock.warehouse")
Quant = model("stock.quant")

projects = Project.search(
    [("project_code", "=like", f"{PREFIX}DA-%")],
    order="project_code",
)
if len(projects) != 30:
    raise AssertionError(
        f"Expected 30 ANL projects before inventory import, found {len(projects)}"
    )
business_projects = projects.filtered(lambda project: project.state != "draft")
if len(business_projects) != 25:
    raise AssertionError(f"Expected 25 non-draft projects, found {len(business_projects)}")

warehouse = Warehouse.search(
    [("company_id", "=", env.company.id)],
    limit=1,
)
if not warehouse:
    raise AssertionError("The company does not have a stock warehouse")
delivery_location = (
    warehouse.out_type_id.default_location_dest_id
    or env.ref("stock.stock_location_customers")
)

request_user = env.ref(
    "dtc_bts_base.user_dtc_ksgs_demo",
    raise_if_not_found=False,
) or env.ref("base.user_admin")

supplier = Partner.search([
    ("partner_type", "=", "supplier"),
    ("active", "=", True),
], order="id", limit=1)
if not supplier:
    raise AssertionError("No existing supplier is available")

unit_uom = env.ref("uom.product_uom_unit")
meter_uom = env.ref("uom.product_uom_meter")
material_category = env.ref(
    "dtc_bts_inventory.product_category_bts_auxiliary",
    raise_if_not_found=False,
) or env.ref("product.product_category_all")
cable_category = env.ref(
    "dtc_bts_inventory.product_category_bts_cable",
    raise_if_not_found=False,
) or material_category
pole_category = env.ref(
    "dtc_bts_inventory.product_category_bts_pole",
    raise_if_not_found=False,
) or material_category

products = model("product.product").search([
    ("product_tmpl_id.is_bts_material", "=", True),
    ("active", "=", True),
], order="id", limit=8)
if len(products) < 8:
    raise AssertionError(
        f"Expected at least 8 existing BTS materials, found {len(products)}"
    )
created = {
    "supplier": 0,
    "products": 0,
    "material_requests": 0,
    "material_request_lines": 0,
    "proposal_material_lines": 0,
    "purchase_orders": 0,
    "receipts": 0,
    "deliveries": 0,
}

def ensure_request(
    name,
    project,
    source,
    request_date,
    requested_products,
    target_state,
    station=None,
    proposal=None,
):
    request_values = {
        "name": name,
        "bts_project_id": project.id,
        "source": source,
        "request_user_id": request_user.id,
        "request_date": request_date,
        "vendor_id": supplier.id,
        "station_id": station.id if station else False,
        "repair_proposal_id": proposal.id if proposal else False,
        "note": (
            "Dữ liệu kho tự động ANL, liên kết theo timeline dự án/bảo trì."
        ),
        "postponement_reason": (
            "Tạm hoãn để chờ xác nhận tiến độ công trình."
            if target_state == "postponed"
            else False
        ),
        "rejection_reason": (
            "Yêu cầu demo bị từ chối do điều chỉnh phương án vật tư."
            if target_state == "rejected"
            else False
        ),
    }
    request, was_created = find_or_create(
        MaterialRequest,
        [("name", "=", name)],
        request_values,
    )
    if not was_created:
        request.with_context(bts_inventory_workflow=True).write(request_values)
    created["material_requests"] += int(was_created)

    for product, quantity in requested_products:
        line = MaterialRequestLine.search([
            ("request_id", "=", request.id),
            ("product_id", "=", product.id),
        ], limit=1)
        line_values = {
            "product_uom_id": product.uom_id.id,
            "quantity_requested": quantity,
            "quantity_approved": (
                0.0
                if target_state in (
                    "draft",
                    "requested",
                    "postponed",
                    "rejected",
                    "cancelled",
                )
                else quantity
            ),
        }
        if line:
            line.write(line_values)
        else:
            MaterialRequestLine.create({
                "request_id": request.id,
                "product_id": product.id,
                **line_values,
            })
            created["material_request_lines"] += 1

    request.with_context(bts_inventory_workflow=True).write({
        "state": target_state,
    })
    return request


def ensure_purchase_order(request, order_date, receive, receipt_date=None):
    purchase_order = PurchaseOrder.search([
        ("bts_material_request_id", "=", request.id),
        ("partner_id", "=", supplier.id),
    ], limit=1)
    if not purchase_order:
        purchase_order = PurchaseOrder.create({
            "partner_id": supplier.id,
            "partner_ref": f"{PREFIX}PO-{request.name}",
            "origin": request.name,
            "date_order": at_noon(order_date),
            "bts_project_id": request.bts_project_id.id,
            "bts_material_request_id": request.id,
            "order_line": [
                (0, 0, {
                    "product_id": line.product_id.id,
                    "name": line.product_id.display_name,
                    "product_qty": line.quantity_approved,
                    "product_uom": line.product_uom_id.id,
                    "price_unit": line.product_id.standard_price,
                    "date_planned": at_noon(
                        receipt_date or order_date + timedelta(days=7)
                    ),
                    "bts_material_request_line_id": line.id,
                })
                for line in request.line_ids
                if line.quantity_approved > 0
            ],
        })
        created["purchase_orders"] += 1

    if purchase_order.state in ("draft", "sent"):
        purchase_order.button_confirm()

    receipt = purchase_order.picking_ids.filtered(
        lambda picking: picking.picking_type_code == "incoming"
    )[:1]
    if not receipt:
        raise AssertionError(f"PO {purchase_order.name} did not create a receipt")

    if receive and receipt.state != "done":
        done_date = safe_business_date(
            receipt_date or order_date + timedelta(days=7)
        )
        receipt.write({"scheduled_date": at_noon(done_date)})
        if receipt.state == "draft":
            receipt.action_confirm()
        receipt.action_assign()
        for move in receipt.move_ids.filtered(
            lambda item: item.state not in ("done", "cancel")
        ):
            move.quantity = move.product_uom_qty
        receipt.with_context(
            skip_backorder=True,
            cancel_backorder=True,
        ).button_validate()
        receipt.write({"date_done": at_noon(done_date)})
        receipt.move_ids.write({"date": at_noon(done_date)})
        created["receipts"] += 1
    elif not receive and receipt.state not in ("done", "cancel"):
        receipt.write({
            "scheduled_date": at_noon(
                receipt_date or order_date + timedelta(days=7)
            ),
        })
    if receive and receipt.state == "done" and purchase_order.state == "purchase":
        purchase_order.button_done()
    return purchase_order, receipt


def ensure_delivery(request, delivery_date, quantities=None):
    delivery = request.picking_ids.filtered(
        lambda picking: picking.picking_type_code == "outgoing"
    )[:1]
    if delivery and delivery.state == "done":
        remaining = {
            line.id: max(
                line.quantity_approved - line.quantity_issued,
                0.0,
            )
            for line in request.line_ids
        }
        if not any(remaining.values()):
            return delivery
        delivery = Picking
        quantities = quantities or remaining

    quantity_by_line = quantities or {
        line.id: line.quantity_approved for line in request.line_ids
    }
    if not delivery:
        moves = []
        for line in request.line_ids:
            quantity = quantity_by_line.get(line.id, 0.0)
            if quantity <= 0:
                continue
            moves.append((0, 0, {
                "name": line.product_id.display_name,
                "product_id": line.product_id.id,
                "product_uom_qty": quantity,
                "product_uom": line.product_uom_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": delivery_location.id,
                "bts_material_request_line_id": line.id,
            }))
        delivery = Picking.create({
            "picking_type_id": warehouse.out_type_id.id,
            "location_id": warehouse.lot_stock_id.id,
            "location_dest_id": delivery_location.id,
            "scheduled_date": at_noon(delivery_date),
            "origin": f"{PREFIX}XUAT-{request.name}",
            "bts_project_id": request.bts_project_id.id,
            "bts_material_request_id": request.id,
            "move_ids_without_package": moves,
        })

    if delivery.state == "draft":
        delivery.action_confirm()
    delivery.action_assign()
    for move in delivery.move_ids.filtered(
        lambda item: item.state not in ("done", "cancel")
    ):
        move.quantity = move.product_uom_qty
    delivery.with_context(
        skip_backorder=True,
        cancel_backorder=True,
    ).button_validate()
    delivery.write({"date_done": at_noon(delivery_date)})
    delivery.move_ids.write({"date": at_noon(delivery_date)})
    created["deliveries"] += 1
    return delivery


# Construction inventory only for the 25 completed projects. Draft projects
# intentionally have no downstream business documents.
construction_requests = []
for project_index, project in enumerate(business_projects, start=1):
    station_count = len(project.task_ids)
    product_start = (project_index - 1) % 4
    request_products = [
        (products[product_start], 40.0 * station_count),
        (products[2], 2.0 * station_count),
        (products[6], 3.0 * station_count),
    ]
    request_date = project.planned_start_date + timedelta(days=14)
    request_name = f"{PREFIX}YC-XD-{project_index:03d}"

    # Repeated distribution supplies every important dashboard state while
    # keeping project/station lifecycle data fully commissioned.
    target_state = (
        "issued",
        "issued",
        "partially_delivered",
        "purchasing",
        "ready",
        "approved",
        "draft",
        "rejected",
        "cancelled",
        "postponed",
    )[(project_index - 1) % 10]

    initial_state = (
        "approved" if target_state in ("issued", "purchasing") else target_state
    )
    request = ensure_request(
        request_name,
        project,
        "project_construction",
        request_date,
        request_products,
        initial_state,
    )
    construction_requests.append(request)

    if target_state == "issued":
        order_date = request_date + timedelta(days=2)
        receipt_date = order_date + timedelta(days=7)
        delivery_date = receipt_date + timedelta(days=4)
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })
        ensure_purchase_order(
            request,
            order_date,
            receive=True,
            receipt_date=receipt_date,
        )
        ensure_delivery(request, delivery_date)
        request.with_context(bts_inventory_workflow=True).write({
            "state": "issued",
        })
    elif target_state == "purchasing":
        order_date = safe_business_date(request_date + timedelta(days=2))
        ensure_purchase_order(
            request,
            order_date,
            receive=False,
            receipt_date=TODAY + timedelta(days=7 + project_index % 5),
        )
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })
    elif target_state == "ready":
        order_date = safe_business_date(request_date + timedelta(days=2))
        receipt_date = safe_business_date(order_date + timedelta(days=7))
        # Keep the request out of automatic notification transitions while
        # its demo receipt is being completed.
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })
        ensure_purchase_order(
            request,
            order_date,
            receive=True,
            receipt_date=receipt_date,
        )
        request.with_context(bts_inventory_workflow=True).write({
            "state": "ready",
        })
    elif target_state == "partially_delivered":
        # Demonstrate a legitimate partial issue from central residual stock.
        order_date = safe_business_date(request_date + timedelta(days=2))
        receipt_date = safe_business_date(order_date + timedelta(days=7))
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })
        ensure_purchase_order(
            request,
            order_date,
            receive=True,
            receipt_date=receipt_date,
        )
        partial_fraction = (0.25, 0.40, 0.55, 0.65, 0.75)[
            project_index % 5
        ]
        partial_quantities = {
            line.id: (
                line.quantity_approved * partial_fraction
                - line.quantity_issued
                if (
                    line.quantity_approved * partial_fraction
                    - line.quantity_issued
                ) >= (line.product_uom_id.rounding or 0.01)
                else 0.0
            )
            for line in request.line_ids
        }
        if any(partial_quantities.values()):
            ensure_delivery(
                request,
                safe_business_date(receipt_date + timedelta(days=2)),
                quantities=partial_quantities,
            )
        request.with_context(bts_inventory_workflow=True).write({
            "state": "partially_delivered",
        })
    elif target_state == "issued":
        order_date = safe_business_date(request_date + timedelta(days=2))
        receipt_date = safe_business_date(order_date + timedelta(days=7))
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })
        ensure_purchase_order(
            request,
            order_date,
            receive=True,
            receipt_date=receipt_date,
        )
        ensure_delivery(
            request,
            safe_business_date(receipt_date + timedelta(days=2)),
        )

# Maintenance inventory: link the ten latest unresolved repair proposals to
# products and material requests. Six are fully issued, two are being
# purchased, and two await approval.
maintenance_proposals = RepairProposal.search([
    ("maintenance_request_id.maintenance_batch_id.name", "=like", f"{PREFIX}BT-%"),
    ("state", "in", ["confirmed", "waiting_material"]),
], order="id desc", limit=10)

for maintenance_index, proposal in enumerate(
    maintenance_proposals.sorted(key=lambda item: item.id),
    start=1,
):
    maintenance_request = proposal.maintenance_request_id
    failure_date = (
        maintenance_request.actual_date
        or maintenance_request.maintenance_batch_id.maintenance_date
        or TODAY
    )
    request_date = safe_business_date(failure_date + timedelta(days=1))
    product = products[4 + ((maintenance_index - 1) % 4)]
    quantity = 1.0 if product.uom_id == unit_uom else 5.0

    proposal_material_line = ProposalMaterialLine.search([
        ("proposal_id", "=", proposal.id),
        ("product_id", "=", product.id),
    ], limit=1)
    if not proposal_material_line:
        ProposalMaterialLine.create({
            "proposal_id": proposal.id,
            "product_id": product.id,
            "product_uom_qty": quantity,
            "product_uom_id": product.uom_id.id,
        })
        created["proposal_material_lines"] += 1

    if maintenance_index <= 6:
        target_state = "issued"
    elif maintenance_index <= 8:
        target_state = "purchasing"
    else:
        target_state = "requested"

    maintenance_initial_state = (
        "approved" if target_state in ("issued", "purchasing") else target_state
    )
    request = ensure_request(
        f"{PREFIX}YC-BT-{maintenance_index:03d}",
        maintenance_request.bts_project_id,
        "maintenance",
        request_date,
        [(product, quantity)],
        maintenance_initial_state,
        station=maintenance_request.station_id,
        proposal=proposal,
    )

    if target_state == "issued":
        order_date = safe_business_date(request_date + timedelta(days=1))
        receipt_date = safe_business_date(order_date + timedelta(days=1))
        delivery_date = safe_business_date(receipt_date + timedelta(days=1))
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })
        ensure_purchase_order(
            request,
            order_date,
            receive=True,
            receipt_date=receipt_date,
        )
        ensure_delivery(request, delivery_date)
        request.with_context(bts_inventory_workflow=True).write({
            "state": "issued",
        })
    elif target_state == "purchasing":
        order_date = safe_business_date(request_date + timedelta(days=1))
        ensure_purchase_order(
            request,
            order_date,
            receive=False,
            receipt_date=TODAY + timedelta(days=5 + maintenance_index),
        )
        request.with_context(bts_inventory_workflow=True).write({
            "state": "purchasing",
        })

    proposal._sync_material_state()

# Consistency audit. Any failure aborts the transaction before commit.
generated_requests = MaterialRequest.search([
    ("name", "=like", f"{PREFIX}YC-%"),
])
generated_purchase_orders = PurchaseOrder.search([
    ("bts_material_request_id.name", "=like", f"{PREFIX}YC-%"),
])
generated_pickings = Picking.search([
    ("bts_material_request_id.name", "=like", f"{PREFIX}YC-%"),
])

# Existing demo pickings may keep dates from an older project timeline. Repair
# them after the project dates are regenerated so chronology remains request ->
# receipt -> delivery.
for request in generated_requests:
    done_receipts = generated_pickings.filtered(
        lambda picking:
        picking.bts_material_request_id == request
        and picking.picking_type_code == "incoming"
        and picking.state == "done"
        and picking.date_done
    ).sorted("date_done")
    previous_date = request.request_date
    for receipt in done_receipts:
        normalized_date = max(receipt.date_done.date(), previous_date)
        receipt.write({"date_done": at_noon(normalized_date)})
        receipt.move_ids.write({"date": at_noon(normalized_date)})
        previous_date = normalized_date

    done_deliveries = generated_pickings.filtered(
        lambda picking:
        picking.bts_material_request_id == request
        and picking.picking_type_code == "outgoing"
        and picking.state == "done"
        and picking.date_done
    ).sorted("date_done")
    for delivery in done_deliveries:
        normalized_date = max(delivery.date_done.date(), previous_date)
        delivery.write({"date_done": at_noon(normalized_date)})
        delivery.move_ids.write({"date": at_noon(normalized_date)})
        previous_date = normalized_date

assert len(construction_requests) == 25
assert len(generated_requests.filtered(
    lambda request: request.source == "project_construction"
)) == 25
assert all(request.line_ids for request in generated_requests)
assert all(
    line.quantity_requested > 0
    and 0 <= line.quantity_approved <= line.quantity_requested
    and 0 <= line.quantity_issued <= line.quantity_approved
    for line in generated_requests.mapped("line_ids")
)
assert all(
    order.bts_project_id == order.bts_material_request_id.bts_project_id
    for order in generated_purchase_orders
)
assert all(
    picking.bts_project_id == picking.bts_material_request_id.bts_project_id
    for picking in generated_pickings
)
assert all(
    picking.date_done.date()
    >= picking.bts_material_request_id.request_date
    for picking in generated_pickings.filtered(
        lambda picking: picking.state == "done" and picking.date_done
    )
)

for product in products:
    available = Quant._get_available_quantity(
        product,
        warehouse.lot_stock_id,
        strict=False,
    )
    if available < 0:
        raise AssertionError(
            f"Negative stock for {product.default_code}: {available}"
        )

env.cr.commit()

print("ANALYTICS_INVENTORY_IMPORT_OK")
print("Created this run:", created)
print(
    "Dataset totals:",
    {
        "products": len(products),
        "material_requests": len(generated_requests),
        "request_lines": len(generated_requests.mapped("line_ids")),
        "purchase_orders": len(generated_purchase_orders),
        "receipts": len(generated_pickings.filtered(
            lambda picking: picking.picking_type_code == "incoming"
        )),
        "deliveries": len(generated_pickings.filtered(
            lambda picking: picking.picking_type_code == "outgoing"
        )),
        "done_pickings": len(generated_pickings.filtered(
            lambda picking: picking.state == "done"
        )),
        "pending_pickings": len(generated_pickings.filtered(
            lambda picking: picking.state not in ("done", "cancel")
        )),
    },
)
