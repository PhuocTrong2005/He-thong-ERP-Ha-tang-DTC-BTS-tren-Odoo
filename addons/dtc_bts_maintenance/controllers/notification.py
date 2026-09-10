from markupsafe import escape

from odoo import _, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class BtsMaintenanceNotificationController(http.Controller):

    def _confirmation_page(self, project, error=None):
        error_html = (
            '<p style="color:#b42318">%s</p>' % escape(error)
            if error
            else ''
        )
        body = """
            <!doctype html><html><head><meta charset="utf-8"/>
            <title>Tiếp nhận bàn giao dự án</title></head>
            <body style="font-family:Arial,sans-serif;max-width:640px;
                         margin:48px auto;padding:0 20px;color:#212529">
              <h2>Tiếp nhận bàn giao dự án</h2>{error}
              <p>Dự án: <strong>{project}</strong></p>
              <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf}"/>
                <button type="submit"
                  style="background:#198754;color:white;border:0;
                         padding:10px 16px;cursor:pointer">
                  Xác nhận tiếp nhận
                </button>
              </form>
            </body></html>
        """.format(
            error=error_html,
            project=escape(project.display_name),
            csrf=escape(request.csrf_token()),
        )
        return request.make_response(
            body,
            headers=[('Content-Type', 'text/html; charset=utf-8')],
        )

    @http.route(
        '/dtc_bts_maintenance/project/<int:project_id>/accept_handover',
        type='http',
        auth='user',
        methods=['GET', 'POST'],
    )
    def accept_project_handover(self, project_id, **kwargs):
        project = request.env['project.project'].browse(project_id).exists()
        if not project:
            return request.not_found()
        if request.httprequest.method == 'GET':
            return self._confirmation_page(project)
        try:
            project.action_accept_maintenance_handover()
        except (AccessError, UserError, ValidationError) as error:
            return self._confirmation_page(project, error.args[0])
        return request.redirect(
            '/web#id=%s&model=project.project&view_type=form' % project.id
        )
