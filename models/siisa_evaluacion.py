# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraSiisaEvaluacion(models.Model):
	_name = 'financiera.siisa.evaluacion'
	
	_order = 'create_date desc'
	name = fields.Char('Nombre')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	motivo = fields.Char('Motivo de rechazo')
	producto_id = fields.Many2one('financiera.siisa.producto','Producto')
	oferta = fields.Integer('Oferta')
	cuota_max = fields.Integer('Cuota maxima')
	plazo = fields.Integer('Plazo')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.siisa.evaluacion'))
	
	@api.model
	def create(self, values):
		rec = super(FinancieraSiisaEvaluacion, self).create(values)
		id_informe = self.env.user.company_id.siisa_configuracion_id.get_evaluacion_id()
		rec.update({
			'name': 'SIISA/EVALUACION/' + str(id_informe).zfill(8),
		})
		return rec
