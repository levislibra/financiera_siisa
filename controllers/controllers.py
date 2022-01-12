# -*- coding: utf-8 -*-
from openerp import http

# class FinancieraSiisa(http.Controller):
#     @http.route('/financiera_siisa/financiera_siisa/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/financiera_siisa/financiera_siisa/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('financiera_siisa.listing', {
#             'root': '/financiera_siisa/financiera_siisa',
#             'objects': http.request.env['financiera_siisa.financiera_siisa'].search([]),
#         })

#     @http.route('/financiera_siisa/financiera_siisa/objects/<model("financiera_siisa.financiera_siisa"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('financiera_siisa.object', {
#             'object': obj
#         })