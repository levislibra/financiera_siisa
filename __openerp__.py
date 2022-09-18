# -*- coding: utf-8 -*-
{
    'name': "Financiera Siisa",

    'summary': """
        Modulo que conecta con motor de decision Siisa e informes crediticios""",

    'description': """
        Modulo que conecta con motor de decision Siisa e informes crediticios
    """,

    'author': "Librasoft",
    'website': "https://libra-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'financiera_prestamos', 'financiera_app'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/extends_res_company.xml',
        'views/siisa_configuracion.xml',
        'views/siisa_evaluacion.xml',
        'views/siisa_informe.xml',
        'views/siisa_cda.xml',
        'views/extends_res_partner.xml',
        'reports/siisa_reports.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}