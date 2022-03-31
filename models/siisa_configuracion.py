# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError, Warning
import time
import requests
import json

ENDPOINT_SIISA = 'https://api.motor.siisa.com.ar'

class FinancieraSiisaConfiguracion(models.Model):
	_name = 'financiera.siisa.configuracion'

	name = fields.Char('Nombre')
	clientId = fields.Integer('Cliente')
	entidadId = fields.Integer('Entidad')
	pinId = fields.Integer('Pin')
	password = fields.Char('Password')
	politicId = fields.Char('Politica')
	id_motor = fields.Integer('Id proxima evaluacion motor', default=1)
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.siisa.configuracion'))

	id_informe = fields.Integer('Id proximo informe', default=1)
	siisa_ejecutar_cda_al_solicitar_informe = fields.Boolean('Ejecutar CDAs al solicitar informe')
	siisa_solicitar_informe_enviar_a_revision = fields.Boolean('Solicitar informe al enviar a revision')
	siisa_variable_1 = fields.Char('Variable 1')
	siisa_variable_2 = fields.Char('Variable 2')
	siisa_variable_3 = fields.Char('Variable 3')
	siisa_variable_4 = fields.Char('Variable 4')
	siisa_variable_5 = fields.Char('Variable 5')
	
	asignar_nombre_cliente = fields.Boolean('Asignar Nombre al cliente')
	asignar_nombre_cliente_variable = fields.Char('Variable para el Nombre', default='VI_RazonSocial')
	
	asignar_direccion_cliente = fields.Boolean('Asignar Direccion al cliente')
	asignar_calle_cliente_variable = fields.Char('Variable para la calle', default='VI_DomAF_Calle')

	asignar_ciudad_cliente = fields.Boolean('Asignar Ciudad a direccion')
	asignar_ciudad_cliente_variable = fields.Char('Variable para la ciudad', default='VI_DomAF_Loc')

	asignar_cp_cliente = fields.Boolean('Asignar CP a direccion')
	asignar_cp_cliente_variable = fields.Char('Variable para el CP', default='VI_DomAF_CP')

	asignar_provincia_cliente = fields.Boolean('Asignar Provincia a direccion')
	asignar_provincia_cliente_variable = fields.Char('Variable para la Provincia', default='VI_DomAF_Prov')

	asignar_identificacion_cliente = fields.Boolean('Asignar identificacion al cliente')
	asignar_identificacion_cliente_variable = fields.Char('Variable para la identificacion', default='VI_Identificacion')

	asignar_genero_cliente = fields.Boolean('Asignar genero al cliente')
	asignar_genero_cliente_variable = fields.Char('Variable para genero', default='VI_Sexo')



	def get_evaluacion_id(self):
		ret = self.id_motor
		self.id_motor += 1
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
		if login != None and 'access_token' in login:
			raise Warning("La cuenta esta conectada.")
		else:
			raise UserError("Error de conexion.")
class FinancieraSiisaProducto(models.Model):
	_name = 'financiera.siisa.producto'

	name = fields.Char('Nombre')
	partner_tipo_id = fields.Many2one('financiera.partner.tipo', 'Tipo de cliente')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.siisa.producto'))

class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	siisa_configuracion_id = fields.Many2one('financiera.siisa.configuracion', 'Configuracion Siisa')
