# Inspecciones [![codecov](https://codecov.io/gh/gomac-un/inspecciones_back/branch/main/graph/badge.svg?token=URPWTW7Z57)](https://codecov.io/gh/gomac-un/inspecciones_back)
Ejecutar el proyecto:
```
sudo apt install virtualenv
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```
Para cargar datos de prueba en una base de datos limpia se usan estos comandos:
```
python manage.py migrate
python manage.py collectstatic
python manage.py loaddata organizacion_usuarios_y_perfiles
python manage.py loaddata activo_cuestionario_inspeccion
python manage.py loaddata organizacion2
```
El usuario gato tiene contraseña gato.

Para ejecutar el servidor con nginx y gunicorn se debe configurar primero nginx con la configuracion adjunta y se usan estos comandos:
```
sudo systemctl restart nginx
gunicorn inspecciones_back.wsgi -b 127.0.0.1:8000 --pid /tmp/gunicorn.pid --daemon
```
para detener el gunicorn, por ejemplo si se actualiza el server:
```
ps ax|grep gunicorn
kill {pid}
```

### comandos utiles
Para guardar datos de prueba, se crean primero en la db ya sea con linea de comandos
o con la interfaz de usuario y se se usa el comando:
```
python manage.py dumpdata > dump.json
```

Ejecutar codigo en un archivo en el shell de django:
```
Get-Content script.py | python manage.py shell
```
