import requests
from django.conf import settings
from django.db import connections, DatabaseError

def validar_recaptcha(recaptcha_response):
    """
    Valida la respuesta de reCAPTCHA con el servidor de Google.
    """
    data = {
        'secret': settings.RECAPTCHA_PRIVATE_KEY,
        'response': recaptcha_response,
    }
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
        response.raise_for_status()
        result = response.json()
        return result.get('success', False)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al validar reCAPTCHA: {str(e)}")
        return False

def configurar_conexion_dinamica(empresa):
    """
    Configura una conexión dinámica a la base de datos de la empresa.
    """
    db_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': empresa.nombre_db,
        'USER': empresa.usuario,
        'PASSWORD': empresa.contraseña,
        'HOST': empresa.host,
        'PORT': empresa.puerto,
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'OPTIONS': {},
        'TIME_ZONE': 'America/Caracas',
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
    }
    connections.databases[empresa.nombre] = db_config

def ejecutar_consulta(cursor, tipo_consulta, documento):
    """
    Ejecuta la consulta SQL según el tipo de consulta.
    """
    if tipo_consulta == 'cedula':
        query = """
            SELECT 
                nic AS numero_contrato,
                situacion, 
                fechasituacion, 
                tipopersona,
                nombre, 
                primerapellido, 
                segundoapellido,
                tipodocumento, 
                cedularif AS cedula, 
                deudatotal
            FROM public.vistainfocomercial
            WHERE cedularif = %s AND cedularif IS NOT NULL AND nic IS NOT NULL
            ORDER BY fechasituacion DESC;
        """
    else:  # tipo_consulta == 'nic'
        query = """
            SELECT 
                nic AS numero_contrato,
                situacion, 
                fechasituacion, 
                tipopersona,
                nombre, 
                primerapellido, 
                segundoapellido,
                tipodocumento, 
                cedularif AS cedula, 
                deudatotal
            FROM public.vistainfocomercial
            WHERE nic = %s AND cedularif IS NOT NULL AND nic IS NOT NULL
            ORDER BY fechasituacion DESC;
        """
    cursor.execute(query, [documento])
    return cursor.fetchall()  # Devuelve todos los resultados