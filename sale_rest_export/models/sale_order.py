# -*- coding: utf-8 -*-
#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from openerp import models, fields, _, api
from openerp.exceptions import ValidationError
from collections import OrderedDict
import json


class SaleOrder(models.Model):
    _inherit = "sale.order"

    chunk_identifier = fields.Integer()
    export_state_info = fields.Char()
    export_content = fields.Char()

    @api.multi
    def _prepare_export_vals(self, exporter):
        """ rtype: dict of format sale_order_id:vals """
        result = OrderedDict()
        self = self.sorted(key=lambda r: r.id)
        for rec in self:
            try:
                addresses = rec._prepare_export_addresses()
                lines = rec._prepare_export_lines()
                amount = rec._prepare_export_amount()
                invoice = rec._prepare_export_invoice()
                payment = rec._prepare_export_payment()
                misc = rec._prepare_misc(exporter)
            except Exception as e:
                rec.export_state_info = str(e)
                continue
            rec.export_state_info = "Exportable"
            vals = dict()
            for el in (addresses, lines, amount, invoice, payment, misc):
                vals.update(el)
            result[rec.id] = vals
            rec.export_content = json.dumps(vals)
        return result

    def _prepare_export_addresses(self):
        result = dict()
        mapping = {
            "address_customer": "partner_id",
            "address_invoicing": "partner_invoice_id",
            "address_shipping": "partner_shipping_id",
        }
        for k, v in mapping.items():
            partner_to_copy = getattr(self, v)
            result[k] = self._prepare_export_partner(partner_to_copy)
        result["address_customer"]["external_id"] = self._find_partner_external_id(
            self.partner_id
        )
        return result

    def _find_partner_external_id(self, partner):
        return str(partner.id)

    def _prepare_export_partner(self, partner):
        result = dict()
        if partner.zip == 0:
            raise ValidationError(_("Absent value for Zip code"))
        fields_required = ["name", "street", "zip", "city", "email"]
        for field in fields_required:
            val = getattr(partner, field)
            if not val:
                raise ValidationError(_("Absent value for %s" % field))
            result.update({field: val})
        fields_optional = ["street2"]
        for field in fields_optional:
            val = getattr(partner, field)
            if val:
                result.update({field: val})
        if partner.state_id:
            result.update({"state_code": partner.state_id.code})
        result.update({"country_code": partner.country_id.code})
        return result

    def _prepare_export_lines(self):
        result = {"lines": []}
        for line in self.order_line:
            vals = {
                "product_code": line.product_id.default_code,
                "qty": line.product_uom_qty,
                "price_unit": line.price_unit,
                "description": line.name,
                "discount": line.discount,
            }
            required_fields = ["product_code", "qty", "price_unit"]
            if not all([vals[required] for required in required_fields]):
                raise ValidationError(_("Invalid line data. Make sure product code, quantity, and price are set for all products"))
            result["lines"].append(vals)
        return result

    def _prepare_export_amount(self):
        return {
            "amount": {
                "amount_tax": self.amount_tax,
                "amount_untaxed": self.amount_untaxed,
                "amount_total": self.amount_total,
            }
        }

    def _prepare_export_invoice(self):
        invoice = self.invoice_ids
        if len(invoice.ids) == 0:
            return {}
        if len(invoice.ids) < 1:
            raise ValidationError(_("There should not be more than one invoice"))
        return {"invoice": {"date": invoice.date_invoice, "number": invoice.name}}

    def _prepare_export_payment(self):
        payment_transaction = self.env["payment.transaction"].search(
            [("reference", "=", self.name)]
        )
        if len(payment_transaction.ids) == 0:
            return {}
        if len(payment_transaction.ids) < 1:
            raise ValidationError(_("There should not be more than one invoice"))
        return {
            "payment": {
                "mode": payment_transaction.acquirer_id.name,
                "amount": payment_transaction.amount,
                "reference": payment_transaction.acquirer_reference,
                "currency_code": payment_transaction.currency_id.name,
                "transaction_id": payment_transaction.id,
            }
        }

    def _prepare_misc(self, exporter):
        mapping = exporter.pricelist_mappings.filtered(
            lambda r: r.local_db_id == self.pricelist_id.id
        )
        if not mapping:
            raise ValidationError("No matching pricelist found")
        return {"currency_code": self.currency_id.name, "pricelist_id": mapping.ext_db_id}
