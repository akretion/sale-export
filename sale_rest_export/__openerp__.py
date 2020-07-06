# -*- coding: utf-8 -*-
#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    "name": "Sale REST Export Base",
    "version": "8.0.1.0.0",
    "author": "Akretion",
    "website": "www.akretion.com",
    "license": "AGPL-3",
    "depends": ["sale"],
    "data": [
        "views/sale_order.xml",
        "views/sale_rest_exporter.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
