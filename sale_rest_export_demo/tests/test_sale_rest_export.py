#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from .common import SaleExportCase
from openerp.tools import float_compare
from mock import patch, MagicMock
import json

class TestSaleRestExport(SaleExportCase):
    def setUp(self):
        super(TestSaleRestExport, self).setUp()

    def test_vals_preparation(self):
        vals = self.sale_order_1._prepare_export_vals(self.exporter)[
            self.sale_order_1.id
        ]
        self.assertEqual(vals["address_customer"]["name"], "Agrolait")
        self.assertEqual(vals["address_shipping"]["name"], "Delta PC")
        self.assertEqual(vals["address_invoicing"]["name"], "China Export")
        self.assertEqual(len(vals["lines"]), 3)
        self.assertEqual(vals["payment"]["mode"], "Adyen")
        self.assertEqual(vals["invoice"]["date"], self.invoice.date_invoice)
        self.assertEqual(
            float_compare(vals["amount"]["amount_untaxed"], 210.00, precision_digits=2),
            0,
        )
        self.assertEqual(vals["pricelist_id"], 456)

    def test_export_basic(self):
        mock_request = MagicMock()
        mock_request.status_code = 200
        mock_request.content = u'{"chunk_ids" : [0,1,2,3,4]}'
        with patch("requests.post", return_value=mock_request):
            self.exporter.button_export_sale_orders()
        self.assertEqual(self.sale_order_1.chunk_identifier, 4)

    def test_reset_chunk_identifiers(self):
        mock_request = MagicMock()
        mock_request.status_code = 200
        mock_request.content = u'{"chunk_ids" : [0,1,2,3,4]}'
        with patch("requests.post", return_value=mock_request):
            self.exporter.button_export_sale_orders()
        self.exporter.button_reset_chunk_identifiers()
        self.assertEqual(self.sale_order_1.chunk_identifier, False)
