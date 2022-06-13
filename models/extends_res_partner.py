# -*- coding: utf-8 -*-

from re import sub
from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
from datetime import datetime
import requests
import json

from zeep import Client
from datetime import date
import xmltodict
from dateutil.parser import parse

ENDPOINT_SIISA_MOTOR = 'https://api.motor.siisa.com.ar'
ENDPOINT_SIISA_INFO = 'https://www.siisa.com.ar/service/siisainfo.asmx?WSDL'
class ExtendsResPartnerSiisa(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	siisa_evaluacion_ids = fields.One2many('financiera.siisa.evaluacion', 'partner_id', 'SIISA - Evaluaciones')
	siisa_ingreso = fields.Char(related='app_ingreso')
	siisa_oferta = fields.Integer('SIISA Oferta')
	siisa_cuota_max = fields.Integer('SIISA Cuota maxima')
	siisa_plazo = fields.Integer('SIISA Plazo')
	siisa_motivo = fields.Char('SIISA Motivo de rechazo')
	siisa_producto_id = fields.Many2one('financiera.siisa.producto','SIISA Producto')
	siisa_capacidad_pago_mensual = fields.Float('SIISA - CPM', digits=(16,2))
	siisa_partner_tipo_id = fields.Many2one('financiera.partner.tipo', 'SIISA - Tipo de cliente')

	# integracion informes SIISA
	siisa_informe_ids = fields.One2many('financiera.siisa.informe', 'partner_id', 'SIISA - Informes')
	siisa_variable_ids = fields.One2many('financiera.siisa.informe.variable', 'partner_id', 'Variables')
	siisa_fecha_ultimo_informe = fields.Datetime('Fecha ultimo informe')
	siisa_variable_1 = fields.Char('Variable 1')
	siisa_variable_2 = fields.Char('Variable 2')
	siisa_variable_3 = fields.Char('Variable 3')
	siisa_variable_4 = fields.Char('Variable 4')
	siisa_variable_5 = fields.Char('Variable 5')
	siisa_capacidad_pago_mensual_copy = fields.Float('SIISA - CPM', digits=(16,2), related='siisa_capacidad_pago_mensual')
	siisa_partner_tipo_id_copy = fields.Many2one('financiera.partner.tipo', 'SIISA - Tipo de cliente', related='siisa_partner_tipo_id')

	def is_int(self, value):
		try:
			int(value)
			return True
		except ValueError:
			return False

	def is_float(self, value):
		try:
			float(value)
			return True
		except ValueError:
			return False

	def is_date(self, value, fuzzy=False):
		try: 
			parse(value, fuzzy=fuzzy)
			return True
		except ValueError:
			return False

	def process_dict(self, parent_key, key, value, list_values, profundidad):
		siisa_configuracion_id = self.company_id.siisa_configuracion_id
		type = None
		if value and isinstance(value, dict):
			for sub_key, sub_value in value.iteritems():
				if key:
					self.process_dict(key, sub_key, sub_value, list_values, profundidad+1)
				else:
					self.process_dict("", sub_key, sub_value, list_values, profundidad+1)
		elif value and isinstance(value, list):
			i = 1
			for sub_value in value:
				self.process_dict(key, key+"_"+str(i), sub_value, list_values, profundidad+1)
				i += 1
		elif value and self.is_int(value):
			type = 'Numero'
			value = str(value)
		elif value and self.is_float(value):
			type = 'Decimal'
			value = str(value)
		elif value and self.is_date(value):
			type = 'Fecha'
			value = str(value)
		else:
			type = 'Texto'
		if not value:
			value = 'None'
		if type:
			# Hack profundida 
			if parent_key == '' or parent_key == None:
				profundidad = 20
			if parent_key == 'Persona':
				profundidad = 0
			if parent_key == 'Scoring':
				profundidad = 0
			if 'Laboral' in parent_key or 'Domicilio' in parent_key:
				profundidad = 1
			if 'MorosidadBCRA' in parent_key:
				profundidad = 2
			variable_nombre = key
			variable_valor = value
			variable_tipo = type
			variable_values = {
					'partner_id': self.id,
					'name': variable_nombre,
					'valor': variable_valor,
					'tipo': variable_tipo,
					'profundidad': profundidad,
					'sub_name': parent_key,
				}
			list_values.append((0,0, variable_values))
			if siisa_configuracion_id.asignar_nombre_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_nombre_cliente_variable:
					self.name = variable_valor
			if siisa_configuracion_id.asignar_direccion_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_calle_cliente_variable:
					self.street = variable_valor
			if siisa_configuracion_id.asignar_ciudad_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_ciudad_cliente_variable:
					self.city = variable_valor			
			if siisa_configuracion_id.asignar_cp_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_cp_cliente_variable:
					self.zip = variable_valor
			if siisa_configuracion_id.asignar_provincia_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_provincia_cliente_variable:
					self.set_provincia(variable_valor)
			if siisa_configuracion_id.asignar_identificacion_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_identificacion_cliente_variable:
					self.main_id_number = variable_valor
			if siisa_configuracion_id.asignar_genero_cliente:
				if variable_nombre == siisa_configuracion_id.asignar_genero_cliente_variable:
					if variable_valor == 'M':
						self.sexo = 'masculino'
					elif variable_valor == 'F':
						self.sexo = 'femenino'
	

	@api.one
	def solicitar_informe_siisa(self):
		siisa_configuracion_id = self.company_id.siisa_configuracion_id
		if not self.dni:
			raise ValidationError("Identidad del cliente no definida!")
		dias_para_consultar_nuevo_informe = siisa_configuracion_id.dias_para_consultar_nuevo_informe
		dias_ultimo_informe = 0
		if self.siisa_fecha_ultimo_informe:
			fecha_ultimo_informe = datetime.strptime(self.siisa_fecha_ultimo_informe, "%Y-%m-%d %H:%M:%S")
			fecha_actual = datetime.now()
			diferencia = fecha_actual - fecha_ultimo_informe
			dias_ultimo_informe = diferencia.days
		print('siisa_fecha_ultimo_informe: ', self.siisa_fecha_ultimo_informe)
		print('dias_para_consultar_nuevo_informe: ', dias_para_consultar_nuevo_informe)
		print('dias_ultimo_informe: ', dias_ultimo_informe)
		if not self.siisa_fecha_ultimo_informe or dias_ultimo_informe >= dias_para_consultar_nuevo_informe:
			print('Entro a la consulta!!')
			client = Client(ENDPOINT_SIISA_INFO)
			ayn = ''
			nroDoc = int(self.dni)
			cuil = 0
			sexo = ''
			if self.sexo == 'masculino':
				sexo = 'M'
			elif self.sexo == 'femenino':
				sexo = 'F'
			data = client.service.GetSiisa(
				1,
				siisa_configuracion_id.entidadId,
				siisa_configuracion_id.pinId,
				siisa_configuracion_id.password,
				nroDoc,
				cuil,
				ayn,
				sexo,
				0,0,date.today(),0,0,0,0,'',''
			)
			data = xmltodict.parse(data['GetSiisaResult'], dict_constructor=dict)
			if 'Consulta' in data and 'DatosSalida' in data['Consulta']:
				nuevo_informe_id = self.env['financiera.siisa.informe'].create({})
				self.siisa_informe_ids = [nuevo_informe_id.id]
				self.siisa_variable_ids = [(6, 0, [])]
				self.siisa_fecha_ultimo_informe = datetime.now()
				list_values = []
				self.process_dict("", "", data['Consulta']['DatosSalida'], list_values, 0)
				nuevo_informe_id.write({'variable_ids': list_values})
				self.siisa_asignar_variables()
				siisa_configuracion_id.id_informe += 1
				if siisa_configuracion_id.siisa_ejecutar_cda_al_solicitar_informe:
					nuevo_informe_id.ejecutar_cdas()

	@api.one
	def siisa_asignar_variables(self):
		variable_1 = False
		variable_2 = False
		variable_3 = False
		variable_4 = False
		variable_5 = False
		siisa_configuracion_id = self.company_id.siisa_configuracion_id
		for var_id in self.siisa_variable_ids:
			if var_id.name == siisa_configuracion_id.siisa_variable_1:
				variable_1 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == siisa_configuracion_id.siisa_variable_2:
				variable_2 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == siisa_configuracion_id.siisa_variable_3:
				variable_3 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == siisa_configuracion_id.siisa_variable_4:
				variable_4 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == siisa_configuracion_id.siisa_variable_5:
				variable_5 = var_id.name + ": " + str(var_id.valor)
		self.write({
			'siisa_variable_1': variable_1,
			'siisa_variable_2': variable_2,
			'siisa_variable_3': variable_3,
			'siisa_variable_4': variable_4,
			'siisa_variable_5': variable_5,
		})

	@api.one
	def set_provincia(self, provincia):
		if provincia == 'Capital Federal':
			provincia = 'Ciudad Autónoma de Buenos Aires'
		state_obj = self.pool.get('res.country.state')
		state_ids = state_obj.search(self.env.cr, self.env.uid, [
			('name', '=ilike', provincia)
		])
		if len(state_ids) > 0:
			self.state_id = state_ids[0]
			country_id = state_obj.browse(self.env.cr, self.env.uid, state_ids[0]).country_id
			self.country_id = country_id.id

	@api.one
	def ejecutar_cdas_siisa(self):
		if self.siisa_informe_ids and len(self.siisa_informe_ids) > 0:
			self.siisa_informe_ids[0].ejecutar_cdas()

	@api.one
	def button_solicitar_informe_siisa(self):
		self.solicitar_informe_siisa()

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
					'ingreso_declarado': int(self.siisa_ingreso),
					'nroDoc': int(self.dni),
				}
			}
			data_json = json.dumps(body)
			endpoint_politic = ENDPOINT_SIISA_MOTOR+'/api/Requests/ExecutePolicyWithDetail/'+str(siisa_configuracion_id.politicId)
			r = requests.post(endpoint_politic, data=data_json, headers=headers)
			if r.status_code == 200:
				data = r.json()
				if data != None and 'variables' in data:
					oferta = 0
					cuota_max = 0
					plazo = 0
					motivo = ""
					producto_id = False
					id_prodcuto = False
					id_partner_tipo = False
					if 'oferta' in data['variables'] and data['variables']['oferta'] != None:
						oferta = data['variables']['oferta'].split('.')[0]
					if 'cuota_max' in data['variables'] and data['variables']['cuota_max'] != None:
						cuota_max = data['variables']['cuota_max'].split('.')[0]
					if 'plazo' in data['variables'] and data['variables']['plazo'] != None:
						plazo = data['variables']['plazo']
					if 'motivo' in data['variables'] and data['variables']['motivo'] != None:
						motivo = data['variables']['motivo']
					if 'producto' in data['variables'] and data['variables']['producto'] != None:
						producto_nombre = data['variables']['producto']
						producto_obj = self.pool.get('financiera.siisa.producto')
						producto_ids = producto_obj.search(self.env.cr, self.env.uid, [
							('company_id','=', self.company_id.id),
							('name', '=', producto_nombre),
						])
						if producto_ids:
							producto_id = producto_obj.browse(self.env.cr, self.env.uid, producto_ids[0])
							id_prodcuto = producto_id.id
							id_partner_tipo = producto_id.partner_tipo_id.id
					values = {
						'oferta': oferta,
						'cuota_max': cuota_max,
						'plazo': plazo,
						'motivo': motivo,
						'producto_id': id_prodcuto,
					}
					nueva_evaluacion_id = self.env['financiera.siisa.evaluacion'].create(values)
					self.write({
						'siisa_oferta': oferta,
						'siisa_cuota_max': cuota_max,
						'siisa_plazo': plazo,
						'siisa_motivo': motivo,
						'siisa_producto_id': id_prodcuto,
						'siisa_capacidad_pago_mensual': int(cuota_max),
						'capacidad_pago_mensual': int(cuota_max),
						'siisa_partner_tipo_id': id_partner_tipo,
						'partner_tipo_id': id_partner_tipo,
					})
					self.siisa_evaluacion_ids = [nueva_evaluacion_id.id]
			else:
				raise ValidationError("Error al realizar la consulta: " + r.text)
		else:
			raise ValidationError("Error de configuracion Siisa")
