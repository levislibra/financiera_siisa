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
	siisa_producto_id = fields.Many2one('financiera.siisa.producto','Siisa Producto')
	siisa_ingreso = fields.Char(related='app_ingreso')
	siisa_oferta = fields.Integer('Siisa Oferta')
	siisa_cuota_max = fields.Integer('Siisa Cuota maxima')
	siisa_plazo = fields.Integer('Siisa Plazo')
	siisa_motivo = fields.Char('Siisa Motivo de rechazo')
	siisa_capacidad_pago_mensual = fields.Float('Siisa - CPM', digits=(16,2))
	siisa_partner_tipo_id = fields.Many2one('financiera.partner.tipo', 'Siisa - Tipo de cliente')

	@api.one
	def siisa_evaluar(self):
		siisa_configuracion_id = self.company_id.siisa_configuracion_id
		login = siisa_configuracion_id.login()
		if login != None and 'access_token' in login:
			access_token = login['access_token']
			headers = {'accept': 'text/plain', 'Content-Type': 'application/json',  'authorization': "Bearer " + access_token}
			siisa_producto_id = self.siisa_producto_id
			if siisa_producto_id == None or siisa_producto_id == False:
				siisa_producto_id = siisa_configuracion_id.producto_id
			if siisa_producto_id == False or siisa_producto_id.name == False:
				raise ValidationError("Error de configuracion de producto")
			body = {
				'params': {
					'apellidoNombre': self.name,
					'ingreso_declarado': int(self.siisa_ingreso),
					'nroDoc': int(self.dni),
					'producto': siisa_producto_id.name,
				}
			}
			print("SIISA: ", body)
			data_json = json.dumps(body)
			endpoint_politic = ENDPOINT_SIISA+'/api/Requests/ExecutePolicyWithDetail/'+str(siisa_configuracion_id.politicId)
			r = requests.post(endpoint_politic, data=data_json, headers=headers)
			print("r: ", r)
			print("r.status_code: ", r.status_code)
			if r.status_code == 200:
				data = r.json()
				print("data: ", data)
				if data != None and 'variables' in data:
					oferta = 0
					cuota_max = 0
					plazo = 0
					motivo = ""
					if 'oferta' in data['variables'] and data['variables']['oferta'] != None:
						oferta = data['variables']['oferta']
					if 'cuota_max' in data['variables'] and data['variables']['cuota_max'] != None:
						cuota_max = data['variables']['cuota_max']
					if 'plazo' in data['variables'] and data['variables']['plazo'] != None:
						plazo = data['variables']['plazo']
					if 'motivo' in data['variables'] and data['variables']['motivo'] != None:
						motivo = data['variables']['motivo']
					values = {
						'oferta': oferta,
						'cuota_max': cuota_max,
						'plazo': plazo,
						'motivo': motivo,
					}
					nueva_evaluacion_id = self.env['financiera.siisa.evaluacion'].create(values)
					print("VALUES: ", values)
					self.write({
						'siisa_oferta': oferta,
						'siisa_cuota_max': cuota_max,
						'siisa_plazo': plazo,
						'siisa_motivo': motivo,
						'siisa_capacidad_pago_mensual': int(cuota_max),
						'capacidad_pago_mensual': int(cuota_max),
					})
					self.siisa_evaluacion_ids = [nueva_evaluacion_id.id]
			else:
				raise ValidationError("Error al realizar la consulta: " + r.text)
		else:
			raise ValidationError("Error de configuracion Siisa")
