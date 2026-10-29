# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 20 pour DGET',
    'version'  : '20.0.0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 20 pour DGET
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        'account',
        'l10n_fr_account',
        'sale',
        'purchase',
        'product',
        'is_theme_entreprise',  # couleur de l'entreprise (module générique)
        'is_interface_epuree',  # page de connexion épurée, inscription sur invitation (module générique)
    ],
    'data' : [
        'security/res.groups.xml',
        'security/ir.model.access.csv',
        'security/ir.model.access.xml',
        'views/res_partner_views.xml',
        'views/is_dossier_views.xml',
        'views/account_invoice_view.xml',
        'views/is_account_invoice_line_views.xml',
        'views/menu.xml',
        'report/report_templates.xml',
        'report/report_invoice.xml',
        'report/report_is_dossier.xml',
        'report/report_is_declaration_maf.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
