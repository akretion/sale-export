# -*- coding: utf-8 -*-
#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import requests
import json
from openerp.tools import safe_eval


class SaleRestExporter(models.Model):
    _name = "sale.rest.exporter"

    name = fields.Char(required=True)
    url_importer = fields.Char(
        "Url of Odoo instance importing Sale Orders", required=True
    )
    api_key = fields.Char("API key to be used for Sale Order export", required=True)
    domain = fields.Char(
        "Domain of Sale orders to be used",
        default="[]",
        help="Exporting and resetting chunks will apply to Sale Orders of this domain",
    )
    count_sale_orders_has_chunk = fields.Integer(
        "Sale Orders with set chunk", compute="_compute_counts"
    )
    count_sale_orders_exportable = fields.Integer(
        "Sale Orders with exportable status", compute="_compute_counts"
    )
    count_sale_orders_error = fields.Integer(
        "Sale Orders with exportable status", compute="_compute_counts"
    )
    count_sale_orders_in_domain = fields.Integer(
        "Sale Orders in domain", compute="_compute_counts"
    )
    pricelist_mappings = fields.One2many(
        "sale.rest.exporter.mapping.line", "exporter_id"
    )

    @api.multi
    def write(self, vals):
        if "domain" in vals:
            try:
                safe_eval(vals["domain"])
            except Exception as e:
                raise ValidationError(_("Bad domain"))
        res = super(SaleRestExporter, self).write(vals)
        return res

    @property
    def domain_has_chunk(self):
        return [("chunk_identifier", "!=", 0)]

    @property
    def domain_exportable(self):
        return [("export_state_info", "=", "Exportable")]

    @property
    def domain_error(self):
        return                 [
                    "&",
                    ("export_state_info", "!=", "Exportable"),
                    ("export_state_info", "!=", False),
                ]

    @property
    def domain_self(self):
        return                 safe_eval(self.domain)

    @api.multi
    def _compute_counts(self):
        for rec in self:
            rec.count_sale_orders_has_chunk = self.env["sale.order"].search_count(
                rec.domain_has_chunk
            )
            rec.count_sale_orders_exportable = self.env["sale.order"].search_count(
                rec.domain_exportable
            )
            rec.count_sale_orders_error = self.env["sale.order"].search_count(
                rec.domain_error
            )
            rec.count_sale_orders_in_domain = self.env["sale.order"].search_count(
                rec.domain_self
            )

    @api.multi
    def button_open_orders_has_chunk(self):
        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": self.domain_has_chunk
            ,
            "type": "ir.actions.act_window",
        }

    @api.multi
    def button_open_orders_exportable(self):
        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": self.domain_exportable,
            "type": "ir.actions.act_window",
        }

    @api.multi
    def button_open_orders_error(self):
        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": self.domain_error,
            "type": "ir.actions.act_window",
        }

    @api.multi
    def button_open_orders_domain(self):
        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": self.domain_self,
            "type": "ir.actions.act_window",
        }

    @api.multi
    def button_reset_chunk_identifiers(self):
        self.env["sale.order"].search([]).write({"chunk_identifier": 0})

    @api.multi
    def button_export_sale_orders(self):
        self.ensure_one()
        sale_orders = self._get_sale_orders()
        exports = sale_orders._prepare_export_vals(self)
        sale_orders_exportable = self.env["sale.order"].browse(sorted(exports.keys()))
        data = {"sale_orders": [vals for vals in exports.values()]}
        headers = {"API_KEY": self.api_key,
                   "Content-Type": "application/json"}
        result = requests.post(
            self.url_importer, headers=headers, data=json.dumps(data)
        )
        if result.status_code == 200:
            result_content = json.loads(result.content)
            if len(result_content["chunk_ids"]) != len(sale_orders_exportable.ids):
                raise ValidationError(
                    _(
                        "Sale orders exported and chunks received are different lengths !"
                        "\nSale orders: %s"
                        "\nChunk ids: %s" % str(sale_orders_exportable.ids),
                        str(result_content["chunk_ids"]),
                    )
                )
            for itr in range(len(sale_orders_exportable)):
                sale_orders_exportable[itr].chunk_identifier = result_content["chunk_ids"][itr]
        else:
            raise ValidationError(str(result))

    def _get_sale_orders(self):
        sale_orders = self.env["sale.order"].search(safe_eval(self.domain))
        return sale_orders.filtered(lambda r: not r.chunk_identifier)
