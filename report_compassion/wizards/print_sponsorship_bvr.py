# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import datetime

from odoo import api, models, fields, _
from odoo.exceptions import Warning as odooWarning


class PrintSponsorshipBvr(models.TransientModel):
    """
    Wizard for selecting a period and the format for printing
    payment slips of a sponsorship.
    """
    _name = 'print.sponsorship.bvr'

    period_selection = fields.Selection([
        ('this_year', 'Current year'),
        ('next_year', 'Next year'),
    ], default='this_year')
    paper_format = fields.Selection([
        ('report_compassion.3bvr_sponsorship', '3 BVR'),
        ('report_compassion.bvr_sponsorship', 'Single BVR')
    ], default='report_compassion.3bvr_sponsorship')
    date_start = fields.Date(default=lambda s: s.default_start())
    date_stop = fields.Date(default=lambda s: s.default_stop())
    include_gifts = fields.Boolean()
    draw_background = fields.Boolean()
    state = fields.Selection([('new', 'new'), ('pdf', 'pdf')], default='new')
    pdf = fields.Boolean()
    pdf_name = fields.Char(default='sponsorship payment.pdf')
    pdf_download = fields.Binary(readonly=True)
    preprinted = fields.Boolean(
        help='Enable if you print on a payment slip that already has company '
             'information printed on it.'
    )

    @api.model
    def default_start(self):
        start = datetime.today().replace(day=1, month=1)
        return fields.Date.to_string(start.replace(day=1))

    @api.model
    def default_stop(self):
        today = datetime.today()
        return fields.Date.to_string(today.replace(day=31, month=12))

    @api.onchange('period_selection')
    def onchange_period(self):
        today = datetime.today()
        start = fields.Datetime.from_string(self.date_start)
        stop = fields.Datetime.from_string(self.date_stop)
        if self.period_selection == 'this_year':
            start = start.replace(year=today.year)
            stop = stop.replace(year=today.year)
        elif self.period_selection == 'next_year':
            start = start.replace(year=today.year + 1)
            stop = stop.replace(year=today.year + 1)
        self.date_start = start
        self.date_stop = stop

    @api.onchange('pdf')
    def onchange_pdf(self):
        if self.pdf:
            self.draw_background = True
            self.preprinted = False
        else:
            self.draw_background = False

    @api.multi
    def print_report(self):
        """
        Prepare data for the report and call the selected report
        (single bvr / 3 bvr).
        :return: Generated report
        """
        if fields.Date.from_string(self.date_start) >= \
                fields.Date.from_string(self.date_stop):
            raise odooWarning(_("Date stop must be after date start."))
        data = {
            'date_start': self.date_start,
            'date_stop': self.date_stop,
            'gifts': self.include_gifts,
            'doc_ids': self.env.context.get('active_ids'),
            'background': self.draw_background,
            'preprinted': self.preprinted
        }
        records = self.env[self.env.context.get('active_model')].browse(
            data['doc_ids'])
        if self.pdf:
            data['background'] = True
            name = records.name if len(records) == 1 else \
                _('sponsorship payment slips')
            self.pdf_name = name + '.pdf'
            self.pdf_download = base64.b64encode(
                self.env['report'].with_context(
                    must_skip_send_to_printer=True).get_pdf(
                        records.ids, self.paper_format, data=data))
            self.state = 'pdf'
            return {
                'name': 'Download report',
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }
        return self.env['report'].get_action(
            records.ids, self.paper_format, data
        )


class PrintBvrDue(models.TransientModel):
    """
    Wizard for selecting a period and the format for printing
    payment slips of a sponsorship.
    """
    _name = 'print.sponsorship.bvr.due'

    draw_background = fields.Boolean()
    state = fields.Selection([('new', 'new'), ('pdf', 'pdf')], default='new')
    pdf = fields.Boolean()
    pdf_name = fields.Char(default='sponsorship due.pdf')
    pdf_download = fields.Binary(readonly=True)

    @api.multi
    def print_report(self):
        """
        Prepare data for the report
        :return: Generated report
        """
        records = self.env[self.env.context.get('active_model')].browse(
            self.env.context.get('active_ids'))
        data = {
            'background': self.draw_background,
            'doc_ids': records.ids,
        }
        report = 'report_compassion.bvr_due'
        if self.pdf:
            data['background'] = True
            self.pdf_download = base64.b64encode(
                self.env['report'].with_context(
                    must_skip_send_to_printer=True).get_pdf(
                    records.ids, report, data=data))
            self.state = 'pdf'
            return {
                'name': 'Download report',
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }
        return self.env['report'].get_action(
            records.ids, report, data
        )
