# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests
import json

ENDPOINT_SIISA = 'https://api.motor.siisa.com.ar'

class ExtendsResPartnerSiisa(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	siisa_evaluacion_ids = fields.One2many('financiera.siisa.evaluacion', 'partner_id', 'Siisa - Evaluaciones')
	siisa_capacidad_pago_mensual = fields.Float('Siisa - CPM', digits=(16,2))
	siisa_partner_tipo_id = fields.Many2one('financiera.partner.tipo', 'Siisa - Tipo de cliente')

	@api.one
	def siisa_evaluar(self):
		siisa_configuracion_id = self.company_id.siisa_configuracion_id
		login = siisa_configuracion_id.login()
		if login != None and 'access_token' in login:
			access_token = login['access_token']
			headers = {'accept': 'text/plain', 'Content-Type': 'application/json',  'authorization': "Bearer " + access_token}
			body = {
				'params': {
					'apellidoNombre': self.name,
					'ingreso_declarado': int(self.app_ingreso),
					'nroDoc': int(self.dni),
					'producto': 'Estrella',
				}
			}
			data_json = json.dumps(body)
			endpoint_politic = ENDPOINT_SIISA+'/api/Requests/ExecutePolicyWithDetail/'+str(siisa_configuracion_id.politicId)
			r = requests.post(endpoint_politic, data=data_json, headers=headers)
			if r.status_code == 200:
				data = r.json()
				if data != None and 'variables' in data:
					oferta = None
					cuota_max = None
					plazo = None
					motivo = None
					if 'oferta' in data['variables']:
						oferta = data['variables']['oferta']
					if 'cuota_max' in data['variables']:
						cuota_max = data['variables']['cuota_max']
					if 'plazo' in data['variables']:
						plazo = data['variables']['plazo']
					if 'motivo' in data['variables']:
						motivo = data['variables']['motivo']
					nueva_evaluacion_id = self.env['financiera.siisa.evaluacion'].create({
						'oferta': oferta,
						'cuota_max': cuota_max,
						'plazo': plazo,
						'motivo': motivo,
					})
					self.siisa_evaluacion_ids = [nueva_evaluacion_id.id]
		else:
			raise ValidationError("Error de configuracion Siisa")
