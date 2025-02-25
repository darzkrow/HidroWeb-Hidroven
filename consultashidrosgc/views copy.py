from django.shortcuts import render,  get_object_or_404
from django.db import connections, DatabaseError
from .models import Empresa, ResultadoConsulta
from collections import defaultdict
from django.core.paginator import Paginator
import requests
from django.conf import settings
import json
from django.core.cache import cache  # Importar la caché de Django (Redis)
from django.http import JsonResponse


# vista de configuracion db
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
        'CONN_MAX_AGE': 0, # mantiene viva la conexion hasta que devuelve resultados!
        'CONN_HEALTH_CHECKS': False,
    }
    connections.databases[empresa.nombre] = db_config


def index(request):
      return render(request,'hidroweb/consultarnic.html')
   

# vista para verificar  recaptcha google
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
        response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa
        result = response.json()
        return result.get('success', False)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al validar reCAPTCHA: {str(e)}")
        return False



from django.core.cache import cache  # Importar la caché de Django (Redis)
from datetime import timedelta



from django.shortcuts import render
from django.db import connections, DatabaseError
from .models import Empresa
from django.core.paginator import Paginator
import requests
from django.conf import settings

def consultar(request):
    if request.method == 'POST':
        # Validar reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            return render(request, 'hidroweb/consultar.html', {
                'error': 'Por favor, completa el reCAPTCHA.',
                'empresas': Empresa.objects.filter(activo=True),
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            })
        
        if not validar_recaptcha(recaptcha_response):
            return render(request, 'hidroweb/consultar.html', {
                'error': 'Error en la validación de reCAPTCHA. Inténtalo de nuevo.',
                'empresas': Empresa.objects.filter(activo=True),
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            })
        
        # Obtener los datos del formulario
        empresa_id = request.POST.get('empresa_id')
        documento = request.POST.get('documento')
        tipo_consulta = request.POST.get('tipo_consulta')  # Capturar el tipo de consulta
        
        # Obtener la empresa seleccionada (solo si está activa)
        try:
            empresa = Empresa.objects.get(id=empresa_id, activo=True)
        except Empresa.DoesNotExist:
            return render(request, 'hidroweb/consultar.html', {
                'error': 'La hidrológica seleccionada no está disponible.',
                'empresas': Empresa.objects.filter(activo=True),
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            })
        
        # Configurar la conexión dinámica a la base de datos de la empresa
        configurar_conexion_dinamica(empresa)
        
        try:
            with connections[empresa.nombre].cursor() as cursor:
                # Consulta dinámica según el tipo de consulta
                if tipo_consulta == 'cedula':
                    cursor.execute("""
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
                        WHERE cedularif = %s
                        ORDER BY fechasituacion DESC
                        LIMIT 1;
                    """, [documento])  # Asegurar que la cédula tenga 9 dígitos
                else:  # tipo_consulta == 'nic'
                    cursor.execute("""
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
                        WHERE nic = %s
                        ORDER BY fechasituacion DESC
                        LIMIT 1;
                    """, [documento])
                
                # Obtener el resultado
                columnas = [column[0] for column in cursor.description]
                resultado = dict(zip(columnas, cursor.fetchone())) if cursor.rowcount > 0 else None
            
            if resultado:
                print(f"[REMOTA] Resultado encontrado para el documento: {documento}, Tipo: {tipo_consulta}")
            else:
                print(f"[REMOTA] No se encontraron resultados para el documento: {documento}, Tipo: {tipo_consulta}")
        
        except DatabaseError as e:
            print(f"[ERROR] Error en la consulta SQL: Empresa: {empresa.nombre}, Error: {str(e)}")
            return render(request, 'hidroweb/consultar.html', {
                'error': f"Error en la consulta: intente más tarde",
                'empresas': Empresa.objects.filter(activo=True),
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            })
        except Exception as e:
            print(f"[ERROR] Error inesperado: Empresa: {empresa.nombre}, Error: {str(e)}")
            return render(request, 'hidroweb/consultar.html', {
                'error': f"Error inesperado: intente más tarde",
                'empresas': Empresa.objects.filter(activo=True),
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            })
        
        # Formatear el resultado para la plantilla
        if resultado:
            datos_finales = [{
                'numero_contrato': resultado.get('numero_contrato'),
                'cedula': resultado.get('cedula'),
                'nombrecompleto': f"{resultado.get('nombre')} {resultado.get('primerapellido')} {resultado.get('segundoapellido')}",
                'situacion': resultado.get('situacion'),
                'fechasituacion': resultado.get('fechasituacion'),
                'deudatotal': resultado.get('deudatotal'),
                
            }]
        else:
            datos_finales = [{
                'numero_contrato': resultado.get('numero_contrato'),
                'cedula': resultado.get('cedula'),
                'nombrecompleto': f"{resultado.get('nombre')} {resultado.get('primerapellido')} {resultado.get('segundoapellido')}",
                'situacion': resultado.get('situacion'),
                'fechasituacion': resultado.get('fechasituacion'),
                'deudatotal': resultado.get('deudatotal'),
                
            }]
        
        # Paginar los resultados (aunque solo habrá uno)
        paginator = Paginator(datos_finales, 10)  # 10 resultados por página
        page_number = request.GET.get('page')  # Obtener el número de página desde la URL
        page_obj = paginator.get_page(page_number)
        
        # Renderizar los resultados
        return render(request, 'hidroweb/resultados.html', {
            'page_obj': page_obj,  # Pasar el objeto de paginación
            'empresa': empresa,    # Pasar el objeto empresa completo
            'documento': documento,  # Pasar el documento
            'tipo_consulta': tipo_consulta,  # Pasar el tipo de consulta
        })
    else:
        # Mostrar el formulario con las empresas activas
        empresas = Empresa.objects.filter(activo=True)
        return render(request, 'hidroweb/consultar.html', {
            'empresas': empresas,
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
        })