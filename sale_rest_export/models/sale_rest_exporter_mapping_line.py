# -*- coding: utf-8 -*-
#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from openerp import models, fields


class SaleRestExporter(models.Model):
    _name = "sale.rest.exporter.mapping.line"

    exporter_id = fields.Many2one("sale.rest.exporter", ondelete="cascade")
    local_db_id = fields.Integer()
    ext_db_id = fields.Integer()
