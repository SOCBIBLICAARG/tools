#!/bin/bash
ODOOENV=/opt/odoo/prod
DATABASE=odoo_prod
SERVICE=odoo-prod-server
USER=odoo_prod

timestamp=$(date +%Y-%m-%d.%H:%M:%S)
logfile=log/update.${timestamp}.log

exec 1>> ${logfile} 2>&1

echo -#- Start Update.
cd $ODOOENV

echo -#- Detenemos el servidor de homologación.
sudo -s service $SERVICE stop

echo -#- Backup de la base de datos.
sudo -u $USER odooenv snapshot $DATABASE

echo -#- Hacemos un update de los modulos.
sudo -u $USER odooenv update

echo -#- Habilitamos todos los modulos.
sudo -u $USER odooenv enable -i fl_sale all

echo -#- Actualizamos los modulos
sudo -u $USER odooenv start --debug -- -u all -d odoo_prod --stop-after-init

echo -#- Reiniciamos el servidor.
sudo -s service $SERVICE start

echo -#- Update terminado.
