from markupsafe import escape

from odoo import _, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class BtsContractNotificationController(http.Controller):

    def _reason_page(self, title, action_url, error=None):
        error_html = (
            '<p style="color:#b42318">%s</p>' % escape(error)
            if error
            else ''
        )
        body = """
            <!doctype html><html><head><meta charset="utf-8"/>
            <title>{title}</title></head>
            <body style="font-family:Arial,sans-serif;max-width:640px;
                         margin:48px auto;padding:0 20px;color:#212529">
              <h2>{title}</h2>{error}
              <form method="post" action="{action}">
                <input type="hidden" name="csrf_token" value="{csrf}"/>
                <label for="reason"><strong>Lý do</strong></label>
                <textarea id="reason" name="reason" required rows="6"
                  style="display:block;width:100%;box-sizing:border-box;
                         margin:8px 0 16px;padding:10px"></textarea>
                <button type="submit"
                  style="background:#b42318;color:white;border:0;
                         padding:10px 16px;cursor:pointer">Xác nhận từ chối</button>
              </form>
            </body></html>
        """.format(
            title=escape(title),
            error=error_html,
            action=escape(action_url),
            csrf=escape(request.csrf_token()),
        )
        return request.make_response(
            body,
            headers=[('Content-Type', 'text/html; charset=utf-8')],
        )

    def _record_url(self, record):
        return '/web#id=%s&model=%s&view_type=form' % (
            record.id,
            record._name,
        )

    @http.route(
        '/dtc_bts_contract/signature_batch/<int:batch_id>/seen',
        type='http',
        auth='user',
        methods=['GET'],
    )
    def mark_signature_batch_notification_seen(self, batch_id, **kwargs):
        batch = request.env['bts.contract.signature.batch'].browse(
            batch_id
        ).exists()
        if not batch:
            return request.not_found()
        batch.action_mark_dashboard_notification_seen()
        action = request.env.ref(
            'dtc_bts_base.action_dtc_bts_dashboard'
        )
        return request.redirect(f'/web#action={action.id}')

    @http.route(
        '/dtc_bts_contract/signature_batch/<int:batch_id>/reject',
        type='http',
        auth='user',
        methods=['GET', 'POST'],
    )
    def reject_signature_batch(self, batch_id, reason=None, **kwargs):
        batch = request.env['bts.contract.signature.batch'].browse(
            batch_id
        ).exists()
        if not batch:
            return request.not_found()
        if request.httprequest.method == 'GET':
            return self._reason_page(
                _('Từ chối ký hồ sơ hợp đồng'),
                request.httprequest.path,
            )
        reason = (reason or '').strip()
        if not reason:
            return self._reason_page(
                _('Từ chối ký hồ sơ hợp đồng'),
                request.httprequest.path,
                _('Lý do từ chối là bắt buộc.'),
            )
        try:
            batch.write({'rejection_reason': reason})
            batch.action_reject()
        except (AccessError, UserError, ValidationError) as error:
            return self._reason_page(
                _('Từ chối ký hồ sơ hợp đồng'),
                request.httprequest.path,
                error.args[0],
            )
        return request.redirect(self._record_url(batch))

    @http.route(
        '/dtc_bts_contract/renewal/<int:renewal_id>/reject',
        type='http',
        auth='user',
        methods=['GET', 'POST'],
    )
    def reject_renewal_signature(self, renewal_id, reason=None, **kwargs):
        renewal = request.env['bts.contract.renewal'].browse(
            renewal_id
        ).exists()
        if not renewal:
            return request.not_found()
        if request.httprequest.method == 'GET':
            return self._reason_page(
                _('Từ chối ký hồ sơ gia hạn'),
                request.httprequest.path,
            )
        reason = (reason or '').strip()
        if not reason:
            return self._reason_page(
                _('Từ chối ký hồ sơ gia hạn'),
                request.httprequest.path,
                _('Lý do từ chối là bắt buộc.'),
            )
        try:
            renewal.write({'rejection_reason': reason})
            renewal.action_reject_signature()
        except (AccessError, UserError, ValidationError) as error:
            return self._reason_page(
                _('Từ chối ký hồ sơ gia hạn'),
                request.httprequest.path,
                error.args[0],
            )
        return request.redirect(self._record_url(renewal))
