#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from openerp.tests.common import SavepointCase
from datetime import datetime


class SaleExportCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(SaleExportCase, cls).setUpClass()
        cls.adyen = cls.env.ref("payment_adyen.payment_acquirer_adyen")

        cls.sale_order_2 = cls.env.ref("sale_rest_export_demo.sale_order_export_demo_2")
        cls.sale_order_2.action_button_confirm()
        cls.invoice = cls.sale_order_2.action_invoice_create()

        cls.sale_order_1 = cls.env.ref("sale_rest_export_demo.sale_order_export_demo_1")
        cls.sale_order_1.action_button_confirm()
        cls.invoice = cls.env["account.invoice"].browse(
            cls.sale_order_1.action_invoice_create()
        )
        cls.invoice.date_invoice = datetime.today().strftime("%Y-%m-%d %H:%M")
        cls.payment_transaction = cls.env["payment.transaction"].create(
            {
                "date_create": (datetime.today()).strftime("%Y-%m-%d %H:%M"),
                "acquirer_id": cls.adyen.id,
                "type": "server2server",
                "state": "done",
                "amount": 210.00,
                "currency_id": cls.env.ref("base.USD").id,
                "partner_country_id": cls.sale_order_1.partner_id.country_id.id,
                "reference": cls.sale_order_1.name,
            }
        )
        cls.exporter = cls.env.ref("sale_rest_export_demo.demo_exporter")