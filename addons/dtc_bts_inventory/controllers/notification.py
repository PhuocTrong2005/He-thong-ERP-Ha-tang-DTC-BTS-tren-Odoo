from markupsafe import escape

from odoo import _, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class BtsInventoryNotificationController(http.Controller):

    def _action_page(
        self,
        title,
        action_url,
        button_label,
        reason_label=None,
        error=None,
    ):
        reason_html = ''
        if reason_label:
            reason_html = """
                <label for="reason"><strong>{label}</strong></label>
                <textarea id="reason" name="reason" required rows="6"
                  style="display:block;width:100%;box-sizing:border-box;
                         margin:8px 0 16px;padding:10px"></textarea>
            """.format(label=escape(reason_label))
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
                {reason}
                <button type="submit"
                  style="background:#714b67;color:white;border:0;
                         padding:10px 16px;cursor:pointer">{button}</button>
              </form>
            </body></html>
        """.format(
            title=escape(title),
            error=error_html,
            action=escape(action_url),
            csrf=escape(request.csrf_token()),
            reason=reason_html,
            button=escape(button_label),
        )
        return request.make_response(
            body,
            headers=[('Content-Type', 'text/html; charset=utf-8')],
        )

    def _record_url(self, material_request):
        return '/web#id=%s&model=bts.material.request&view_type=form' % (
            material_request.id,
        )

    def _material_request(self, request_id):
        return request.env['bts.material.request'].browse(request_id).exists()

    @http.route(
        '/dtc_bts_inventory/notification/<int:notification_id>/seen',
        type='http',
        auth='user',
        methods=['GET'],
    )
    def mark_notification_seen(self, notification_id, **kwargs):
        notification = request.env['bts.material.notification'].browse(
            notification_id
        ).exists()
        if not notification:
            return request.not_found()
        notification_type = notification.notification_type
        notification.action_mark_seen()
        action = request.env.ref(
            (
                'dtc_bts_base.action_dtc_bts_dashboard'
                if notification_type == 'ready'
                else 'dtc_bts_inventory.'
                'action_dtc_bts_inventory_dashboard'
            )
        )
        return request.redirect(f'/web#action={action.id}')

    @http.route(
        '/dtc_bts_inventory/material_request/<int:request_id>/approve',
        type='http',
        auth='user',
        methods=['GET', 'POST'],
    )
    def approve_material_request(self, request_id, **kwargs):
        material_request = self._material_request(request_id)
        if not material_request:
            return request.not_found()
        if request.httprequest.method == 'GET':
            return self._action_page(
                _('Duyệt yêu cầu vật tư'),
                request.httprequest.path,
                _('Xác nhận duyệt'),
            )
        try:
            material_request.action_approve()
        except (AccessError, UserError, ValidationError) as error:
            return self._action_page(
                _('Duyệt yêu cầu vật tư'),
                request.httprequest.path,
                _('Xác nhận duyệt'),
                error=error.args[0],
            )
        return request.redirect(self._record_url(material_request))

    @http.route(
        '/dtc_bts_inventory/material_request/<int:request_id>/reject',
        type='http',
        auth='user',
        methods=['GET', 'POST'],
    )
    def reject_material_request(self, request_id, reason=None, **kwargs):
        return self._material_reason_action(
            request_id,
            reason,
            _('Từ chối yêu cầu vật tư'),
            _('Xác nhận từ chối'),
            'rejection_reason',
            'action_reject',
        )

    @http.route(
        '/dtc_bts_inventory/material_request/<int:request_id>/postpone',
        type='http',
        auth='user',
        methods=['GET', 'POST'],
    )
    def postpone_material_request(self, request_id, reason=None, **kwargs):
        return self._material_reason_action(
            request_id,
            reason,
            _('Tạm hoãn yêu cầu vật tư'),
            _('Xác nhận tạm hoãn'),
            'postponement_reason',
            'action_postpone',
        )

    def _material_reason_action(
        self,
        request_id,
        reason,
        title,
        button_label,
        field_name,
        action_name,
    ):
        material_request = self._material_request(request_id)
        if not material_request:
            return request.not_found()
        if request.httprequest.method == 'GET':
            return self._action_page(
                title,
                request.httprequest.path,
                button_label,
                reason_label=_('Lý do bắt buộc'),
            )
        reason = (reason or '').strip()
        if not reason:
            return self._action_page(
                title,
                request.httprequest.path,
                button_label,
                reason_label=_('Lý do bắt buộc'),
                error=_('Vui lòng nhập lý do.'),
            )
        try:
            material_request.write({field_name: reason})
            getattr(material_request, action_name)()
        except (AccessError, UserError, ValidationError) as error:
            return self._action_page(
                title,
                request.httprequest.path,
                button_label,
                reason_label=_('Lý do bắt buộc'),
                error=error.args[0],
            )
        return request.redirect(self._record_url(material_request))
