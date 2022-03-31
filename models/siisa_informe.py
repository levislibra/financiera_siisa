# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraSiisaInforme(models.Model):
	_name = 'financiera.siisa.informe'
	
	_order = 'create_date desc'
	name = fields.Char('Nombre')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	# Nueva integracion
	variable_ids = fields.One2many('financiera.siisa.informe.variable', 'informe_id', 'Variables')
	cda_resultado_ids = fields.One2many('financiera.siisa.cda.resultado', 'informe_id', 'Resultados')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.siisa.informe'))
	
	@api.model
	def create(self, values):
		rec = super(FinancieraSiisaInforme, self).create(values)
		id_informe = self.env.user.company_id.siisa_configuracion_id.id_informe
		rec.update({
			'name': 'SIISA/INFORME/' + str(id_informe).zfill(8),
		})
		return rec

	@api.one
	def ejecutar_cdas(self):
		cda_obj = self.pool.get('financiera.siisa.cda')
		cda_ids = cda_obj.search(self.env.cr, self.env.uid, [
			('activo', '=', True),
			('company_id', '=', self.company_id.id),
		])
		if len(cda_ids) > 0:
			self.partner_id.siisa_capacidad_pago_mensual = 0
			self.partner_id.capacidad_pago_mensual = 0
			self.partner_id.siisa_partner_tipo_id = None
			self.partner_id.partner_tipo_id = None
		for _id in cda_ids:
			cda_id = cda_obj.browse(self.env.cr, self.env.uid, _id)
			ret = cda_id.ejecutar(self.id)
			if ret['resultado'] == 'aprobado':
				self.partner_id.siisa_capacidad_pago_mensual = ret['cpm']
				self.partner_id.capacidad_pago_mensual = ret['cpm']
				self.partner_id.siisa_partner_tipo_id = ret['partner_tipo_id']
				self.partner_id.partner_tipo_id = ret['partner_tipo_id']
				break

class FinancierasiisaInformeVariable(models.Model):
	_name = 'financiera.siisa.informe.variable'
	
	_order = 'profundidad asc, sub_name asc'
	informe_id = fields.Many2one('financiera.siisa.informe', 'Informe')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	name = fields.Char('Nombre')
	valor = fields.Char('Valor')
	fecha = fields.Date('Fecha')
	descripcion = fields.Char('Descripcion')
	tipo = fields.Char('Tipo')
	sub_name = fields.Char('Nombre pariente')
	profundidad = fields.Integer('Profundidad')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.siisa.informe.variable'))
	