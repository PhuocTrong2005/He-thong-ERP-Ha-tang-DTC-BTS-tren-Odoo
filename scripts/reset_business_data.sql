\set ON_ERROR_STOP on

-- Reset transactional/demo data while preserving Odoo configuration and the
-- master data explicitly required by the project:
-- users, companies, partners, maintenance checklist/category, and materials.
BEGIN;

CREATE TEMP TABLE reset_preserved_counts AS
SELECT
    (SELECT count(*) FROM res_users) AS users_count,
    (SELECT count(*) FROM res_company) AS companies_count,
    (SELECT count(*) FROM res_partner) AS partners_count,
    (SELECT count(*) FROM maintenance_equipment_category) AS maintenance_categories_count,
    (SELECT count(*) FROM bts_maintenance_checklist_item) AS checklist_items_count,
    (SELECT count(*) FROM product_template WHERE is_bts_material) AS material_templates_count,
    (SELECT count(*) FROM product_product WHERE is_bts_material) AS material_variants_count;

-- Generic Odoo resources do not have database foreign keys to their business
-- records, so remove their references explicitly before truncating the records.
DELETE FROM ir_attachment
WHERE res_model IN (
    'bts.contract',
    'bts.contract.renewal',
    'bts.contract.signature.batch',
    'bts.contract.signature.batch.line',
    'bts.maintenance.batch',
    'bts.maintenance.checklist.result',
    'bts.material.notification',
    'bts.material.request',
    'bts.material.request.line',
    'bts.negotiation.minutes',
    'bts.repair.proposal',
    'bts.repair.proposal.line',
    'bts.repair.proposal.material.line',
    'bts.station.handover',
    'maintenance.equipment',
    'maintenance.request',
    'project.project',
    'project.task',
    'project.update',
    'purchase.order',
    'purchase.order.line',
    'stock.lot',
    'stock.move',
    'stock.move.line',
    'stock.picking',
    'stock.quant',
    'stock.scrap',
    'stock.valuation.layer'
);

DELETE FROM ir_model_data
WHERE model IN (
    'bts.contract',
    'bts.contract.renewal',
    'bts.contract.signature.batch',
    'bts.contract.signature.batch.line',
    'bts.maintenance.batch',
    'bts.maintenance.checklist.result',
    'bts.material.notification',
    'bts.material.request',
    'bts.material.request.line',
    'bts.negotiation.minutes',
    'bts.repair.proposal',
    'bts.repair.proposal.line',
    'bts.repair.proposal.material.line',
    'bts.station.handover',
    'maintenance.equipment',
    'maintenance.request',
    'project.project',
    'project.task',
    'project.update',
    'purchase.order',
    'purchase.order.line',
    'stock.lot',
    'stock.move',
    'stock.move.line',
    'stock.picking',
    'stock.quant',
    'stock.scrap',
    'stock.valuation.layer'
);

-- DELETE is intentionally used instead of TRUNCATE CASCADE. Odoo's database
-- has several reverse links from configuration/master tables to the latest
-- business document; TRUNCATE CASCADE would follow those links too broadly.
DELETE FROM mail_notification;
DELETE FROM mail_mail;
DELETE FROM mail_activity;
DELETE FROM mail_followers;
DELETE FROM mail_message;

DELETE FROM bts_material_notification;
DELETE FROM bts_contract_signature_batch_line;
DELETE FROM bts_contract_signature_batch;
DELETE FROM bts_station_handover;
DELETE FROM bts_contract_renewal;
DELETE FROM bts_negotiation_minutes;
DELETE FROM bts_contract;

DELETE FROM bts_maintenance_checklist_result;
DELETE FROM bts_repair_proposal_material_line;
DELETE FROM bts_repair_proposal_line;
DELETE FROM bts_repair_proposal;
DELETE FROM bts_maintenance_batch;
DELETE FROM maintenance_request;
DELETE FROM maintenance_equipment;
DELETE FROM bts_maintenance_equipment_bulk_wizard;

DELETE FROM stock_valuation_layer;
DELETE FROM stock_move_line;
DELETE FROM stock_package_level;
DELETE FROM stock_move;
DELETE FROM stock_scrap;
DELETE FROM stock_picking;
DELETE FROM stock_quant;
DELETE FROM stock_quant_package;
DELETE FROM stock_lot;
DELETE FROM purchase_order_line;
DELETE FROM purchase_order;
DELETE FROM bts_material_request_line;
DELETE FROM bts_material_request;

DELETE FROM project_collaborator;
DELETE FROM project_milestone;
DELETE FROM project_update;
DELETE FROM project_task_recurrence;
DELETE FROM project_task;
DELETE FROM project_project;

-- Remove stale application notifications that are not database-FK-backed.
DELETE FROM bus_presence;

-- Restart only custom business document numbering. System/configuration
-- sequences remain untouched.
UPDATE ir_sequence
SET number_next = 1
WHERE code LIKE 'dtc.bts.%' OR code LIKE 'bts.%';

DO $$
DECLARE
    before_counts reset_preserved_counts%ROWTYPE;
BEGIN
    SELECT * INTO before_counts FROM reset_preserved_counts;

    IF before_counts.users_count <> (SELECT count(*) FROM res_users)
       OR before_counts.companies_count <> (SELECT count(*) FROM res_company)
       OR before_counts.partners_count <> (SELECT count(*) FROM res_partner)
       OR before_counts.maintenance_categories_count <> (SELECT count(*) FROM maintenance_equipment_category)
       OR before_counts.checklist_items_count <> (SELECT count(*) FROM bts_maintenance_checklist_item)
       OR before_counts.material_templates_count <> (SELECT count(*) FROM product_template WHERE is_bts_material)
       OR before_counts.material_variants_count <> (SELECT count(*) FROM product_product WHERE is_bts_material)
    THEN
        RAISE EXCEPTION 'A preserved master-data count changed; aborting reset';
    END IF;
END
$$;

SELECT
    (SELECT count(*) FROM res_users) AS users_kept,
    (SELECT count(*) FROM res_company) AS companies_kept,
    (SELECT count(*) FROM res_partner) AS partners_kept,
    (SELECT count(*) FROM maintenance_equipment_category) AS maintenance_categories_kept,
    (SELECT count(*) FROM bts_maintenance_checklist_item) AS checklist_items_kept,
    (SELECT count(*) FROM product_template WHERE is_bts_material) AS material_templates_kept,
    (SELECT count(*) FROM product_product WHERE is_bts_material) AS material_variants_kept,
    (SELECT count(*) FROM project_project) AS projects_left,
    (SELECT count(*) FROM bts_contract) AS contracts_left,
    (SELECT count(*) FROM bts_material_request) AS material_requests_left,
    (SELECT count(*) FROM purchase_order) AS purchase_orders_left,
    (SELECT count(*) FROM stock_picking) AS stock_pickings_left,
    (SELECT count(*) FROM stock_quant) AS stock_quants_left,
    (SELECT count(*) FROM maintenance_equipment) AS maintenance_equipment_left,
    (SELECT count(*) FROM maintenance_request) AS maintenance_requests_left;

\if :dry_run
ROLLBACK;
\else
COMMIT;
\endif
