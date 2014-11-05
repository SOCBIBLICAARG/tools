#!/usr/bin/python
# -*- encoding: utf-8 -*-


from ConfigParser import SafeConfigParser
import sys
import xmlrpclib
import pymssql
from datetime import date
from datetime import datetime

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# create logger
#logging.getLogger(__name__).setLevel(logging.DEBUG)
#logging.getLogger(__name__).info('Esta avanzando')

def get_pricelist_id(dict_destino,origin_percent):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']

	res = sock.execute(dbname,uid,pwd,'product.pricelist','search',[('name','like',origin_percent)])
	if res:
		return res[0]
	else:
		return None

def get_payment_term_id(dict_destino,origin_payment_term=''):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	if not origin_payment_term:
		origin_payment_term = ' '
	res = []
	res = sock.execute(dbname,uid,pwd,'account.payment.term','search',[('name','=',origin_payment_term)])
	if res == []:
		return 1
	else:
		return res[0]
###########################################################################################################
def get_location_id(dict_destino,origin_categ=''):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	if not origin_categ:
		origin_categ = ' '
	res = sock.execute(dbname,uid,pwd,'stock.location','search',[('name','like',origin_categ)])

	return res

###########################################################################################################
def get_product_id(dict_destino,origin=''):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	if not origin:
		origin = ' '
	res = sock.execute(dbname,uid,pwd,'product.product','search',[('default_code','=',origin)])

	return res
###########################################################################################################
def get_category_id(dict_destino,origin=''):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	if not origin:
		origin = ' '
	res = sock.execute(dbname,uid,pwd,'res.partner.category','search',[('name','like',origin)])

	return res
###########################################################################################################


def get_afip_type(origin_type,dict_destino):
	
	map_type = {
		'INSCRIPTO': 'IVARI',
		'CONSFIN': 'CF',
		'EXENTO': 'IVAE',
		'MONOTRI': 'RM',
		}
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']

	res = sock.execute(dbname,uid,pwd,'afip.responsability','search',[('code','=',map_type[origin_type])])

	return res[0]

##############################################################################################################
def insert_inventory_line(row,dict_destino,inventory_id):

	vals_inventory_line = {}	
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	try:
		product_id = sock.execute(dbname,uid,pwd,'product.product','search',[('sba_code','=',row['part_no'])])
		if not product_id:
			return None
		vals_inventory_line = {
			'product_id': product_id[0],
			'location_id': get_location_id(dict_destino,row['location'])[0],
			'product_qty': float(row['cantidad']),
			'product_uom_id': 1,
			'company_id': 1,
			'inventory_id': inventory_id
			}
		sock = dict_destino['sock']
		uid = dict_destino['uid']
		dbname = dict_destino['dbname']
		pwd = dict_destino['password']
		return_id = sock.execute(dbname,uid,pwd,'stock.inventory.line','create',vals_inventory_line)
	except:
		print 'ERROR: Inserción linea de inventario'
		print vals_inventory_line
		exit(-1)
	return None
##############################################################################################################
def insert_inventory(dict_destino):

	vals_inventory = {
		'name': 'Inventario Transferencia ' + str(date.today()),
		'state': 'confirm',
		# 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		}
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']

	return_id = sock.execute(dbname,uid,pwd,'stock.inventory','create',vals_inventory)
	
	return return_id
##############################################################################################################
def insert_location(row,dict_destino):
	vals_location = {
		'name': row['location']+' - '+row['name'].decode('cp1252'),
		'usage': 'internal',
		'location_id': 12,
		}
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']

	location_id = sock.execute(dbname,uid,pwd,'stock.location','search',[('name','like',row['location'])])
	return_id = 0
	if not location_id:
		return_id = sock.execute(dbname,uid,pwd,'stock.location','create',vals_location)
	
	return None
##############################################################################################################
def insert_category(row,dict_destino):
	vals_category = {
		'name': row['channel_code'].decode('cp1252'),
		}
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']

	categ_id = sock.execute(dbname,uid,pwd,'res.partner.category','search',[('name','=',row['channel_code'])])
	return_id = 0
	if not categ_id:
		return_id = sock.execute(dbname,uid,pwd,'res.partner.category','create',vals_category)
	return None
##############################################################################################################
def insert_factura_impaga(row,dict_destino):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	insert_flag = False

	logger.debug('Factura leida en EPICOR')
	logger.debug(row)

	if row['CUSTOMER_CODE']:
		partner_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('cod_epicor','=',row['CUSTOMER_CODE'])])
		if not partner_id:
			logger.error("No se encuentra disponible el cliente "+row['CUSTOMER_CODE'])
			return None
		else:
			data_partner = sock.execute(dbname,uid,pwd,'res.partner','read',partner_id,['property_account_receivable'])
			account_id = data_partner[0]['property_account_receivable'][0]
	else:
		logger.error("La factura "+row['DOC_CTRL_NUM']+" no tiene cliente")
		return None
	origin = 'EPICOR - '+row['DOC_CTRL_NUM']
	invoice_id = sock.execute(dbname,uid,pwd,'account.invoice','search',[('origin','=',origin)])
	if not invoice_id:
		state_invoice = 'draft'
		insert_flag = True
	else:
		insert_flag = False
		data_invoice = sock.execute(dbname,uid,pwd,'account.invoice','read',invoice_id,['state'])
		state_invoice = data_invoice[0]['state']
	journal_id = sock.execute(dbname,uid,pwd,'account.journal','search',[('name','ilike','%'+row['DOC_CTRL_NUM'][:3]+'%')])
	if journal_id:
		product_id = sock.execute(dbname,uid,pwd,'product.product','search',[('default_code','=','EPICOR_SALDO')])
		vals_invoice = {
			'account_id': account_id,
			'origin': origin,
			'partner_id': partner_id[0],
			'company_id': 1,
			'journal_id': journal_id[0],
			'type': 'out_invoice',
			}
		vals_line = {
			'name': row['NAME'],
			'product_id': product_id[0],
			'quantity': 1,
			'price_unit': abs(float(row['SALDO'])),
			}
		if row.has_key('DATE_DOC'):
			try:
				vals_invoice['date_invoice'] = str(row['DATE_DOC'].date())
			except:
				vals_invoice['date_invoice'] = str(date.today())
		else:
			vals_invoice['date_invoice'] = str(date.today())
		if row.has_key('DATE_DUE'):
			try:
				vals_invoice['date_due'] = str(row['DATE_DUE'].date())
			except:
				pass
	
		if insert_flag:
			return_id = sock.execute(dbname,uid,pwd,'account.invoice','create',vals_invoice)
			invoice_id = return_id
		else:
			return_id = sock.execute(dbname,uid,pwd,'account.invoice','write',invoice_id,vals_invoice)
			if isinstance(invoice_id,list):
				invoice_id = invoice_id[0]
		vals_line['invoice_id'] = invoice_id
		line_id = sock.execute(dbname,uid,pwd,'account.invoice.line','search',\
				[('product_id','=',product_id[0]),('invoice_id','=',invoice_id)])
		if not line_id:
			return_id = sock.execute(dbname,uid,pwd,'account.invoice.line','create',vals_line)
		else:
			return_id = sock.execute(dbname,uid,pwd,'account.invoice.line','write',line_id,vals_line)
		# if state_invoice == 'draft' or insert_flag:
		#	return_id = sock.exec_workflow(dbname,uid, pwd,'account.invoice', 'invoice_open',invoice_id)
		

	return None

##############################################################################################################
def insert_product(row,dict_destino):
	lst_price = float(row['price_a'])
	cost = float(row['avg_cost'])
	temp_name = row['description']
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']

        product_oldcode = temp_name[:temp_name.find(' ')]
        try:
                temp_number = int(product_oldcode)
                product_name = row['description'][row['description'].find(' ')+1:]
        except ValueError:
                product_name = row['description']
                product_oldcode = ''


	familia_id = sock.execute(dbname,uid,pwd,'product.familia','search',[('name','like',row['category'])])
	if row['freight_class']:
		version_id = sock.execute(dbname,uid,pwd,'product.version','search',[('name','like',row['freight_class'])])
	else:	
		version_id = None
	
	vals_template = {
		'categ_id': 1,
		'company_id': 1,
		'cost_method': 'standard',
		# 'description': row['description'].decode('cp1252'),
		'description': row['description'],
		'list_price': lst_price,
		# 'name': row['description'].decode('cp1252'),
		'name': product_name,
		#'procure_method': 'make_to_stock',
		#'supply_method': 'buy',
		'type': 'product',
		'uom_id': 1,
		'uom_po_id': 1
		}
	vals_product = {
		# 'default_code': row['part_no'],
		'default_code': product_oldcode,
		'code': row['part_no'],
		'lst_price': lst_price,
		'standard_price': cost,
		# 'name_template': row['description'].decode('cp1252'),
		'name_template': product_name,
		# 'description': row['description'].decode('cp1252') + '\n' + row['sku_no'].decode('cp1252') or '',
		'description': row['description']+ '\n' + row['sku_no'] or '',
		'sba_sku_no': row['sku_no'] or '',
		# 'sba_code': product_oldcode,
		'sba_code': row['part_no'],
	}
	if familia_id:
		vals_product['familia'] = familia_id[0]
	if version_id:
		vals_product['version'] = version_id[0]
	if row['tax_code'] == 'IVA21D':
		vals_product['taxes_id'] = [(6,0,[1])]

	# product_code = row['description'].decode('cp1252')
	product_code = row['description']
	# import pdb;pdb.set_trace()
	# product_id = sock.execute(dbname,uid,pwd,'product.product','search',[('default_code','=',row['part_no'])])
	product_id = sock.execute(dbname,uid,pwd,'product.product','search',[('sba_code','=',row['part_no'])])
	# import pdb;pdb.set_trace()
	return_id = 0
	if not product_id:
		template_id = sock.execute(dbname,uid,pwd,'product.template','create',vals_template,{})
		vals_product['product_tmpl_id'] = template_id
		return_id = sock.execute(dbname,uid,pwd,'product.product','create',vals_product,{})
	else:
		data_product = sock.execute(dbname,uid,pwd,'product.product','read',product_id,['product_tmpl_id'])
		template_id = data_product[0]['product_tmpl_id'][0]
		vals_product['product_tmpl_id'] = data_product[0]['product_tmpl_id'][0]
		del vals_template['name']
		del vals_template['description']
		del vals_product['name_template']
		del vals_product['description']
		del vals_product['sba_sku_no']
		if vals_product.has_key('taxes_id'):
			del vals_product['taxes_id']
		return_id = sock.execute(dbname,uid,pwd,'product.template','write',[template_id],vals_template,{})
		product_id = sock.execute(dbname,uid,pwd,'product.product','write',product_id,vals_product,{})
	if row['vendor']:
		supplier_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('ref','=',row['vendor']),('supplier','=',True)])
		if supplier_id:
			supplier_info_id = sock.execute(dbname,uid,pwd,'product.supplierinfo','search',[('product_tmpl_id','=',template_id),\
				('name','=',supplier_id)])
			if not supplier_info_id:
				vals_supplierinfo = {
					'product_tmpl_id': template_id,
					'name': supplier_id[0],
					}
				# import pdb;pdb.set_trace()
				supplierinfo_id = sock.execute(dbname,uid,pwd,'product.supplierinfo','create',vals_supplierinfo)
	return None
##############################################################################################################
def insert_ctacte_saldo(row,dict_destino):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	partner_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('cod_epicor','=',row['customer_code']),('customer','=',True)])
	
	if partner_id:
		# import pdb;pdb.set_trace()
		data = sock.execute(dbname,uid,pwd,'res.partner','read',partner_id,['credit','property_account_receivable'])
		data = data[0]
		credit_amount = data['credit']
		db_amount = 0
		cr_amount = 0
		if int(row['saldo']) <> int(credit_amount):
			if row['saldo'] > credit_amount:
				db_amount = row['saldo'] - credit_amount
				cr_amount = 0
			else:
				cr_amount = credit_amount - row['saldo']
				db_amount = 0
			journal_id = sock.execute(dbname,uid,pwd,'account.journal','search',[('code','=','START')])
			vals_acct_move = {
				'date':str(date.today()),
				'journal_id': journal_id[0],
				}
			move_id = sock.execute(dbname,uid,pwd,'account.move','create',vals_acct_move)
			customer_acct_id = data['property_account_receivable'][0]
			migration_acct_id = sock.execute(dbname,uid,pwd,'account.account','search',[('code','=','360000')])
			vals_cust_line = {
				'name': 'Saldo cliente',
				'partner_id': partner_id[0],
				'account_id': customer_acct_id,
				'debit': db_amount,
				'credit': cr_amount,
				'move_id': move_id
				}
			return_id = sock.execute(dbname,uid,pwd,'account.move.line','create',vals_cust_line)
			vals_migr_line = {
				'name': 'Cuenta saldo inicial',
				'account_id': migration_acct_id[0],
				'debit': cr_amount,
				'credit': db_amount,
				'move_id': move_id
				}
			return_id = sock.execute(dbname,uid,pwd,'account.move.line','create',vals_migr_line)
			return_id = sock.exec_workflow(dbname,uid, pwd,'account.move', 'button_validate',move_id)
			
	return None
##############################################################################################################
def insert_supplier_balance(row,dict_destino):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	partner_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('ref','=',row['vendor_code']),('supplier','=',True)])
	if partner_id:
		data = sock.execute(dbname,uid,pwd,'res.partner','read',partner_id)
		data = data[0]
		debit_amount = data['debit']
		db_amount = 0
		cr_amount = 0
		if int(row['SALDO']) <> int(debit_amount):
			if row['SALDO'] > debit_amount:
				cr_amount = row['SALDO'] - debit_amount
				db_amount = 0
			else:
				db_amount = debit_amount - row['SALDO']
				cr_amount = 0
			journal_id = sock.execute(dbname,uid,pwd,'account.journal','search',[('code','=','START')])
			vals_acct_move = {
				'date':str(date.today()),
				'journal_id': journal_id[0],
				}
			move_id = sock.execute(dbname,uid,pwd,'account.move','create',vals_acct_move)
			customer_acct_id = data['property_account_payable'][0]
			migration_acct_id = sock.execute(dbname,uid,pwd,'account.account','search',[('code','=','360000')])
			vals_cust_line = {
				'name': 'Saldo proveedor',
				'partner_id': partner_id[0],
				'account_id': customer_acct_id,
				'debit': db_amount,
				'credit': cr_amount,
				'move_id': move_id
				}
			return_id = sock.execute(dbname,uid,pwd,'account.move.line','create',vals_cust_line)
			vals_migr_line = {
				'name': 'Cuenta saldo inicial proveedor',
				'account_id': migration_acct_id[0],
				'debit': cr_amount,
				'credit': db_amount,
				'move_id': move_id
				}
			return_id = sock.execute(dbname,uid,pwd,'account.move.line','create',vals_migr_line)
			return_id = sock.exec_workflow(dbname,uid, pwd,'account.move', 'button_validate',move_id)
			
	return None
##############################################################################################################
def insert_supplier(row,dict_destino):
	vals_partner = {
		# 'ref': row['vendor_code'].decode('cp1252'),
		'ref': row['vendor_code'],
		#'name': row['address_name'].decode('cp1252'),
		'name': row['address_name'],
		#'street': row['addr2'].decode('cp1252'),
		'street': row['addr2'] or 'N/A',
		#'city': row['city'].decode('cp1252'),
		'city': row['city'] or 'N/A',
		#'zip': row['postal_code'].decode('cp1252'),
		'zip': row['postal_code'] or 'N/A',
		'is_company': True,
		'document_number': row['tax_id_num'].replace('-',''),
		'responsability_id': get_afip_type('INSCRIPTO',dict_destino),
		'email': row['attention_email'] or row['contact_email'] or 'N/A',
		'phone': row['phone_1'] or 'N/A',
		'mobile': row['attention_phone'] or 'N/A',
		'supplier': True,
		'customer': False,
		'property_payment_term': get_payment_term_id(dict_destino,row['terms_code']),
		'active': True,
		'document_type_id': 25,
		}
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	if vals_partner['document_number'] == '':
		vals_partner['document_number'] = '20000000001'

	partner_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('ref','=',row['vendor_code']),('supplier','=',True)])
	return_id = 0
	if not partner_id:
		try:
			return_id = sock.execute(dbname,uid,pwd,'res.partner','create',vals_partner)
		except:
			logger.error(vals_partner)
			import pdb;pdb.set_trace()
	else:
		try:
			return_id = sock.execute(dbname,uid,pwd,'res.partner','write',partner_id[0],vals_partner)
		except:
			logger.error(vals_partner)
	
	return None
##############################################################################################################
def insert_customer(row,dict_destino):
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	if row['address_name'].find(' '):
		customer_oldcode = row['address_name'][:row['address_name'].find(' ')]
		region = 'N/A'
		correlativo = 'N/A'
		canal = 'N/A'
		try:
			temp_number = int(customer_oldcode)
			customer_name = row['address_name'][row['address_name'].find(' ')+1:]
			region = customer_oldcode[:1]
			canal = customer_oldcode[1:2]
			correlativo = customer_oldcode[2:]
			dict_region = { 
					'1': 'BUE',
					'2': 'ROS',
					'3': 'CBA',
					'4': 'MDQ',
					'5': 'BBA' }
			dict_canal = {
				'1': 'Distribuidor',
				'3': 'Libreria',
				'4': 'Instituciones/Escuelas',
				'5': 'Colptores',
				'6': 'Iglesias',
				'9': 'Iglesias',
				'7': 'Desconocido',
				'8': 'Desconocido',
				}
			region = dict_region[region]
			# import pdb;pdb.set_trace()
			try:
				canal = dict_canal[customer_oldcode[1:2]]
			except:	
				canal = 'N/A'
		except ValueError:
			customer_name = row['address_name']
			customer_oldcode = ''
			if row['customer_code']:
				dict_region = { 
						'BUE': 'BUE',
						'ROS': 'ROS',
						'CBA': 'CBA',
						'MDQ': 'MDQ',
						'BBA': 'BBA' }
				dict_canal = {
					'1': 'Distribuidor',
					'3': 'Libreria',
					'4': 'Instituciones/Escuelas',
					'5': 'Colptores',
					'6': 'Iglesias',
					'9': 'Iglesias',
					'7': 'Desconocido',
					'8': 'Desconocido',
					}
				if row['customer_code'][:3] in dict_region.keys():
					region = dict_region[row['customer_code'][:3]]
	else:
		region = 'N/A'
		correlativo = 'N/A'
		canal = 'N/A'
		customer_name = row['address_name']
		customer_oldcode = ''
	if row['tax_id_num']:
		tax_id_num = row['tax_id_num'].replace('-','')
	else:
		tax_id_num = '20000000001'
	user_id = sock.execute(dbname,uid,pwd,'res.users','search',[('cod_vendedor_epicor','=',row['salesperson_code'])])
	if not user_id:
		# import pdb;pdb.set_trace()
		user_id = 1
	else:
		user_id = user_id[0]
	if (row['phone_1'] is None):
		row['phone_1'] = 'N/A'
	if (row['phone_2'] is None):
		row['phone_2'] = 'N/A'

	region_id = sock.execute(dbname,uid,pwd,'res.partner.region','search',[('name','=',region)]) or 1
	if isinstance(region_id,list):
		region_id = region_id[0]
	else:
		region_id = 1

	vals_partner = {
		#'ref': row['customer_code'].decode('cp1252'),
		'ref': customer_oldcode,
		'cod_epicor': row['customer_code'],
		#'name': row['address_name'].decode('cp1252'),
		'name': customer_name or 'N/A',
		'street': row['addr2'] or 'N/A',
		# 'street': 'N/A',
		'city': row['city'] or 'N/A',
		#'city': row['city'],
		'zip': row['postal_code'] or 'N/A',
		# 'zip': row['postal_code'],
		'is_company': True,
		'document_number': tax_id_num,
		'document_type_id': 25,
		'responsability_id': get_afip_type(row['tax_figure'],dict_destino),
		'category_id': [(6,0,get_category_id(dict_destino,row['ftp']))],
		'credit_limit': row['credit_limit'],
		'email': row['attention_email'] or row['contact_email'] or 'N/A',
		'phone': row['phone_1'].strip() or 'N/A',
		'mobile': row['phone_2'].strip() or 'N/A',
		'property_payment_term': get_payment_term_id(dict_destino,row['terms_code']),
		'comment': row['note'] or '',
		'user_id': user_id,
		'date': str(row['added_by_date'])[:10] or str(date.today())[:10],
		'region': region_id,
		'correlativo': correlativo or 'N/A',
		'canal': canal,
		'active': True,
		# 'property_account_receivable': 235,
		}
	if row['added_by_date']:
		vals_partner['date'] = str(row['added_by_date'])[:10] 
	else:
		vals_partner['date'] = str(date.today())
	pricelist_id = get_pricelist_id(dict_destino,str(int(row['trade_disc_percent'])))
	if pricelist_id:
		vals_partner['property_product_pricelist'] = pricelist_id

	partner_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('ref','=',row['customer_code']),('customer','=',True)])
	if not partner_id:
		partner_id = sock.execute(dbname,uid,pwd,'res.partner','search',[('cod_epicor','=',row['customer_code']),('customer','=',True)])
	# import pdb;pdb.set_trace()

	return_id = 0
	if not partner_id:
		try:
			return_id = sock.execute(dbname,uid,pwd,'res.partner','create',vals_partner)
		except:	
			# import pdb;pdb.set_trace()
			logger.error("Problemas en insercion de partner")
			logger.error(vals_partner)
			pass
	else:
		try:
			return_id = sock.execute(dbname,uid,pwd,'res.partner','write',partner_id,vals_partner)
		except:
			logger.error("Problemas en actualizacion de partner")
			logger.error(vals_partner)
			pass
	return None
##############################################################################################################

def transfer_categorias(dict_origen,dict_destino):

	logger.debug('Iniciando transferencia de categorias de productos')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database='SBA_POS_Backoffice',as_dict=True)
	cur = conn.cursor()

	cur.execute('SELECT distinct channel_code,description FROM pmchannel')
	row = cur.fetchone()

	while row:
		logger.debug(row['description'])
		insert_category(row,dict_destino)
		row = cur.fetchone()
	conn.close()
	logger.debug('Fin transferencias de categorias de productos')


	return None
#################################################################################################################
def transfer_productos(dict_origen,dict_destino):

	logger.debug('Iniciando transferencia de productos')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute("SELECT a.*,b.price_a,c.avg_cost FROM inv_master a join part_price b on a.part_no = b.part_no \
		left join inv_list c on a.part_no = c.part_no where c.location = 'ADC000' and obsolete <> 1 and a.void <> 'Y'")
	row = cur.fetchone()

	while row:
		logger.debug(row)
		insert_product(row,dict_destino)
		row = cur.fetchone()

	conn.close()
	logger.debug('Fin transferencia de productos')

	return None
#################################################################################################################
def transfer_inventarios(dict_origen,dict_destino):

	# import pdb;pdb.set_trace()
	logger.debug('Iniciando transferencia de inventarios')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute('SELECT location,part_no,sum(in_stock) as cantidad FROM inventory where in_stock > 0 group by location,part_no')
	row = cur.fetchone()
	inventory_id = insert_inventory(dict_destino)
	while row:
		logger.debug(row)
		insert_inventory_line(row,dict_destino,inventory_id)
		row = cur.fetchone()

	conn.close()
	logger.debug('Finalizando transferencia de inventarios')

	return None
#################################################################################################################
def transfer_proveedores(dict_origen,dict_destino):
	logger.debug('Iniciando transferencia proveedores')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute("SELECT vendor_code, address_name, addr2, city, state, addr5 AS PAIS,postal_code, attention_name, \
		attention_phone, contact_phone, phone_1, tax_code,tax_id_num, attention_email, contact_email, posting_code, terms_code, \
		 country_code FROM apmaster")
	row = cur.fetchone()

	while row:
		logger.debug(row)
		insert_supplier(row,dict_destino)
		row = cur.fetchone()

	conn.close()
	logger.debug('Fin transferencia de proveedores')
	
	return None
#################################################################################################################
def transfer_ctactes(dict_origen,dict_destino):
	logger.debug('Iniciando transferencia de cuentas corrientes')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database='SBA_POS_Backoffice',as_dict=True)
	cur = conn.cursor()

	cur.execute("SELECT customer_code, ROUND(SUM (amount),2) as saldo FROM dbo.setrxage \
		WHERE org_id = 'SBA' AND branch_code LIKE territory_code \
		 GROUP BY customer_code having round(sum(amount),2) > -1")
	row = cur.fetchone()

	while row:
		logger.debug(row)
		insert_ctacte_saldo(row,dict_destino)
		row = cur.fetchone()

	conn.close()
	logger.debug('Finalizando transferencia de cuentas corrientes')

	return None
#################################################################################################################
def transfer_depositos(dict_origen,dict_destino):

	# import pdb;pdb.set_trace()
	logger.debug('Iniciando transferencia de depositos')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute('SELECT location,name FROM locations')
	row = cur.fetchone()

	while row:
		logger.debug(row)
		insert_location(row,dict_destino)
		row = cur.fetchone()

	conn.close()
	logger.debug('Finalizando transferencia de depositos')

	return None
#################################################################################################################
def transfer_saldos_proveedores(dict_origen,dict_destino):

	logger.debug('Iniciando transferencia de saldos de proveedores')
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute("SELECT a.vendor_code, ROUND(b.amt_balance,2) AS [SALDO] FROM apmaster a INNER JOIN apactvnd b \
		 ON a.vendor_code = b.vendor_code WHERE a.status_type = 5  -- 5 = ESTADO ACTIVO")
	row = cur.fetchone()
	# import pdb;pdb.set_trace()
	while row:
		logger.debug(row)
		if row['SALDO'] > 0:
			insert_supplier_balance(row,dict_destino)
		row = cur.fetchone()

	conn.close()
	logger.debug('Fin transferencia de saldos de proveedores')

	return None

#################################################################################################################
def transfer_facturas_impagas(dict_origen,dict_destino):

	logger.debug("Inicio transferencia facturas impagas desde EPICOR")
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute("SELECT * from OPENINVOICES where DOC_TYPE = 'FAC'")
	row = cur.fetchone()
	while row:
		insert_factura_impaga(row,dict_destino)
		row = cur.fetchone()

	conn.close()

	logger.debug("Fin transferencia facturas impagas desde EPICOR")

	return None
#################################################################################################################
def transfer_pagos_facturas(dict_origen,dict_destino):

	logger.debug("Inicio transferencia de pagos desde EPICOR")
	sock = dict_destino['sock']
	uid = dict_destino['uid']
	dbname = dict_destino['dbname']
	pwd = dict_destino['password']
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	invoice_ids = sock.execute(dbname,uid,pwd,'account.invoice','search',[('origin','like','EPICOR3'),('state','=','draft')])
	journal_id = sock.execute(dbname,uid,pwd,'account.journal','search',[('code','=','BNC2')])
	if isinstance(journal_id,list):
		journal_id = journal_id[0]
	account_id = sock.execute(dbname,uid,pwd,'account.account','search',[('name','=','Banco')])
	if isinstance(account_id,list):
		account_id = account_id[0]
	account_line_id = sock.execute(dbname,uid,pwd,'account.account','search',[('name','=','Deudores por ventas')])
	if isinstance(account_line_id,list):
		account_line_id = account_line_id[0]
	for invoice_id in invoice_ids:
		data_invoice = sock.execute(dbname,uid,pwd,'account.invoice','read',invoice_id)
		origin_nbr = data_invoice['origin'][9:]
		sql_string = "select * from OPENINVOICES where DOC_CTRL_NUM = '"+origin_nbr+"'"
		cur.execute(sql_string)
		row = cur.fetchone()
		if not row:
			
			logger.debug('Factura pagada - '+origin_nbr)
			#vals_voucher = {
			#	'partner_id': data_invoice['partner_id'][0],
			#	'account_id': account_id, 
			#	'comment': 'Pago realizado en Epicor',
			#	'journal_id': journal_id,
                        #       'active': True,
                        #        'date': str(date.today()),
			#	'amount': data_invoice['amount_total'],
                        #        'type': 'receipt',
			#	}
			#voucher_id = sock.execute(dbname,uid,pwd,'account.voucher','create',vals_voucher)
                        #vals_voucher_line = {
                        #        'voucher_id': voucher_id,
                        #        'account_id': account_line_id,
                        #        'type': 'cr',
                        #        'amount': data_invoice['amount_total'],
                        #        'amount_original': data_invoice['amount_total'],
                        #        'move_line_id': data_invoice['move_id'][0],
                        #        'name': data_invoice['origin'],
                        #        'partner_id': data_invoice['partner_id'][0],
                        #        'reconcile': True,
                        #        }
			import pdb;pdb.set_trace()
			# voucher_line_id = sock.execute(dbname,uid,pwd,'account.voucher.line','create',vals_voucher_line)
			
			return_id = sock.execute(dbname,uid,pwd,'account.invoice','unlink',[invoice_id])
			import pdb;pdb.set_trace()
		logger.debug(invoice_id)

	#cur.execute("SELECT * from OPENINVOICES where DOC_TYPE = 'FAC'")
	#row = cur.fetchone()
	#while row:
	#	insert_factura_impaga(row,dict_destino)
	#	row = cur.fetchone()

	conn.close()

	logger.debug("Fin transferencia de pagos desde EPICOR")





#################################################################################################################
def transfer_clientes(dict_origen,dict_destino):

	logger.debug("Iniciando la transferencia de clientes")
	conn = pymssql.connect(host=dict_origen['host'], port=dict_origen['port'],user=dict_origen['user'],\
		password=dict_origen['password'], database=dict_origen['dbname'],as_dict=True)
	cur = conn.cursor()

	cur.execute("SELECT customer_code,address_name,addr2,postal_code,city,tax_id_num,tax_figure,ftp,credit_limit,terms_code,trade_disc_percent,attention_email,contact_email,phone_1,phone_2,note,added_by_date,salesperson_code FROM clientes where status_type = '1' ")
	row = cur.fetchone()
	while row:
		logger.debug(row)
		insert_customer(row,dict_destino)
		row = cur.fetchone()

	conn.close()
	logger.debug("Finalizo la transferencia de clientes")

	return None
#################################################################################################################

def get_openerp_connection(dict_destino):
	res = {}
	if len(sys.argv) == 4:
		if sys.argv[3] == 'prod':	
			server_string = 'https://'+dict_destino['host']+'/xmlrpc/common'
			server_obj_string = 'https://'+dict_destino['host']+'/xmlrpc/object'
	else:
		server_string = 'http://'+dict_destino['host']+':'+dict_destino['port']+'/xmlrpc/common'
		server_obj_string = 'http://'+dict_destino['host']+':'+dict_destino['port']+'/xmlrpc/object'
	try:
		sock_common = xmlrpclib.ServerProxy(server_string)
		uid = sock_common.login(dict_destino['dbname'], dict_destino['user'], dict_destino['password'])

		#replace localhost with the address of the server
		sock = xmlrpclib.ServerProxy(server_obj_string)
	except:
		print "Hay problemas de coneccion con el server Odoo"
		exit(-1)
	res = {
		'sock': sock,
		'uid': uid,
		'dbname': dict_destino['dbname'],
		'password': dict_destino['password'],
		}
	return res


def main():

	parser = SafeConfigParser()
	parser.read(sys.argv[1])

	dict_origen = {
		'host': parser.get('origen','host'),
		'port': parser.get('origen','port'),
		'dbname': parser.get('origen','dbname'),
		'user': parser.get('origen','user'),
		'password': parser.get('origen','password'),
		}

	dict_destino = {
		'host': parser.get('destino','host'),
		'port': parser.get('destino','port'),
		'dbname': parser.get('destino','dbname'),
		'user': parser.get('destino','user'),
		'password': parser.get('destino','password'),
		}

	dict_oerp = get_openerp_connection(dict_destino)
	logger.debug(dict_oerp)

	if sys.argv[2] == 'clientes':
		transfer_clientes(dict_origen,dict_oerp)
	if sys.argv[2] == 'categorias':
		transfer_categorias(dict_origen,dict_oerp)
	if sys.argv[2] == 'productos':
		transfer_productos(dict_origen,dict_oerp)
	if sys.argv[2] == 'depositos':
		transfer_depositos(dict_origen,dict_oerp)
	if sys.argv[2] == 'inventarios':
		transfer_inventarios(dict_origen,dict_oerp)
	if sys.argv[2] == 'ctactes':
		transfer_ctactes(dict_origen,dict_oerp)
	if sys.argv[2] == 'proveedores':
		transfer_proveedores(dict_origen,dict_oerp)
	if sys.argv[2] == 'saldos_proveedores':
		transfer_saldos_proveedores(dict_origen,dict_oerp)
	if sys.argv[2] == 'facturas_impagas':
		transfer_facturas_impagas(dict_origen,dict_oerp)
	if sys.argv[2] == 'pagos_facturas':
		transfer_pagos_facturas(dict_origen,dict_oerp)

	return None

if __name__ == '__main__':
	main()

