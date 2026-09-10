import logging

from odoo import _, fields, models
from odoo.exceptions import AccessError
from odoo.tools import email_normalize


_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    _BTS_TEMPLATE_ONLY_EMAIL_MODELS = frozenset({
        'project.project',
        'project.task',
        'maintenance.equipment',
        'maintenance.request',
    })

    def _bts_uses_template_only_email(self):
        """Return whether generic Odoo emails are disabled for this model."""
        return (
            self._name.startswith('bts.')
            or self._name in self._BTS_TEMPLATE_ONLY_EMAIL_MODELS
        )

    def _notify_thread_by_email(
        self,
        message,
        recipients_data,
        msg_vals=False,
        **kwargs,
    ):
        """Keep chatter/inbox updates but never email Odoo's generic layout.

        BTS business emails are explicitly sent by configured ``mail.template``
        records. This hook covers generic emails caused by chatter posts,
        activity completion, follower updates, and any activity creation path
        that does not use ``mail_activity_quick_update``.
        """
        if self._bts_uses_template_only_email():
            return True
        return super()._notify_thread_by_email(
            message,
            recipients_data,
            msg_vals=msg_vals,
            **kwargs,
        )


class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    def _bts_user_can_read_activity_record(self, user):
        """Return whether ``user`` can open this activity's business record."""
        self.ensure_one()
        if not user or not user.active:
            return False
        record = self.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids,
        )
        if not record.check_access_rights('read', raise_exception=False):
            return False
        try:
            record.check_access_rule('read')
        except AccessError:
            return False
        return True

    def _bts_queue_workflow_email(
        self,
        template_xmlid,
        recipient_users,
        event_key,
        marker_field=None,
        marker_value=None,
        marker_values=None,
        extra_context=None,
    ):
        """Send a BTS workflow email without making the workflow depend on it.

        The caller supplies a business marker (or marker values) when the
        event needs idempotency. Recipients are deduplicated by normalized
        address and checked against the record's ACL and record rules. Delivery
        is delegated to Odoo's queue so transient SMTP errors and provider
        rate limits do not block or burst-send from a business transaction.
        """
        self.ensure_one()
        if self.env.context.get('bts_skip_workflow_email'):
            return False
        if marker_field and self[marker_field]:
            return self.env['mail.mail']

        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            _logger.warning(
                'bts_email_template_missing event=%s template=%s model=%s record_id=%s',
                event_key,
                template_xmlid,
                self._name,
                self.id,
            )
            return self.env['mail.mail']

        recipients_by_email = {}
        for user in recipient_users or self.env['res.users']:
            partner = user.partner_id
            normalized_email = email_normalize(partner.email or '')
            if (
                not user.active
                or not partner.active
                or not normalized_email
                or not self._bts_user_can_read_activity_record(user)
            ):
                continue
            recipients_by_email.setdefault(normalized_email, user)

        if not recipients_by_email:
            _logger.warning(
                'bts_email_no_valid_recipient event=%s template=%s model=%s record_id=%s',
                event_key,
                template_xmlid,
                self._name,
                self.id,
            )
            return self.env['mail.mail']

        base_url = self.get_base_url()
        context_values = {
            'record_url': (
                '%s/web#id=%s&model=%s&view_type=form'
                % (base_url.rstrip('/'), self.id, self._name)
                if base_url
                else False
            ),
        }
        context_values.update(extra_context or {})
        queued_mails = self.env['mail.mail']
        for user in recipients_by_email.values():
            try:
                with self.env.cr.savepoint():
                    mail_id = template.with_context(
                        **context_values,
                        recipient_name=user.name,
                    ).send_mail(
                        self.id,
                        force_send=False,
                        email_values={
                            'email_to': user.email_formatted,
                            'recipient_ids': [(6, 0, [user.partner_id.id])],
                        },
                    )
                    queued_mails |= self.env['mail.mail'].browse(mail_id)
            except Exception:
                _logger.warning(
                    'bts_email_send_failed event=%s template=%s model=%s '
                    'record_id=%s recipient_user_id=%s',
                    event_key,
                    template_xmlid,
                    self._name,
                    self.id,
                    user.id,
                )

        values = dict(marker_values or {})
        if marker_field:
            values[marker_field] = (
                marker_value
                if marker_value is not None
                else fields.Datetime.now()
            )
        if queued_mails and values:
            try:
                with self.env.cr.savepoint():
                    self.with_context(bts_email_marker_write=True).write(values)
            except Exception:
                _logger.warning(
                    'bts_email_marker_write_failed event=%s model=%s record_id=%s',
                    event_key,
                    self._name,
                    self.id,
                )
        return queued_mails

    def _bts_schedule_activity_once(
        self,
        activity_type_xmlid,
        user,
        summary,
        deadline=None,
        note=None,
    ):
        """Create or update one open BTS activity for a record/type/user.

        The narrow sudo searches are intentional: an actor completing a group
        workflow may not own every activity created for the other recipients.
        Business-record access is checked in the recipient's own environment
        before an activity is created.
        """
        self.ensure_one()
        activity_type = self.env.ref(
            activity_type_xmlid,
            raise_if_not_found=False,
        )
        if (
            not activity_type
            or not self._bts_user_can_read_activity_record(user)
        ):
            return self.env['mail.activity']

        activity_model = self.env['mail.activity'].sudo()
        domain = [
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('user_id', '=', user.id),
        ]
        activity = activity_model.search(domain, limit=1)
        values = {
            'summary': summary,
            'date_deadline': deadline or fields.Date.context_today(self),
            'note': note or False,
        }
        if activity:
            activity.write(values)
            return activity

        # ``mail_activity_quick_update`` keeps the activity and its in-app bus
        # update, but prevents Odoo from emailing its generic
        # "<document>: <activity> was assigned to you" notification. BTS
        # workflow emails are sent separately with configured HTML templates.
        self.with_context(mail_activity_quick_update=True).activity_schedule(
            activity_type_id=activity_type.id,
            user_id=user.id,
            summary=values['summary'],
            date_deadline=values['date_deadline'],
            note=values['note'],
        )
        return activity_model.search(domain, limit=1)

    def _bts_close_activities(
        self,
        activity_type_xmlid,
        user=None,
        feedback=None,
    ):
        """Complete only the matching open BTS activities."""
        activity_type = self.env.ref(
            activity_type_xmlid,
            raise_if_not_found=False,
        )
        if not activity_type:
            return False
        activity_model = self.env['mail.activity'].sudo()
        for record in self:
            domain = [
                ('res_model', '=', record._name),
                ('res_id', '=', record.id),
                ('activity_type_id', '=', activity_type.id),
            ]
            if user:
                domain.append(('user_id', '=', user.id))
            activities = activity_model.search(domain)
            if activities:
                activities.action_feedback(
                    feedback=feedback or _('Công việc nghiệp vụ đã được xử lý.')
                )
        return True
