# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError, Warning
import time
import requests
import json

ENDPOINT_SIISA = 'https://api.motor.siisa.com.ar'

class FinancieraNosisConfiguracion(models.Model):
	_name = 'financiera.siisa.configuracion'

	name = fields.Char('Nombre')
	clientId = fields.Integer('Cliente')
	pinId = fields.Integer('Pin')
	password = fields.Char('Password')
	politicId = fields.Char('Politica')
	id_informe = fields.Integer('Id proxima evaluacion', default=1)
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.siisa.configuracion'))

	def get_evaluacion_id(self):
		ret = self.id_informe
		self.id_informe += 1
		return ret

	def login(self):
		data = None
		body = {
			'clientId': self.clientId,
			'pinId': self.pinId,
			'password': self.password,
			'expires_in': 0,
		}
		headers = {'accept': 'text/plain', 'Content-Type': 'application/json'}
		data_json = json.dumps(body)
		r = requests.post(ENDPOINT_SIISA+'/api/Login/Token', data=data_json, headers=headers)
		if r.status_code == 200:
			data = r.json()
		return data

	@api.one
	def button_login_test(self):
		login = self.login()
		print("login: ", login)
		if login != None and 'access_token' in login:
			raise Warning("La cuenta esta conectada.")
		else:
			raise UserError("Error de conexion.")
class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	siisa_configuracion_id = fields.Many2one('financiera.siisa.configuracion', 'Configuracion Siisa')
