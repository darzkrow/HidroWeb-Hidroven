from django.shortcuts import render, get_object_or_404
from django.db import connections, DatabaseError
from .models import Empresa
from django.core.paginator import Paginator
import requests
from django.conf import settings
from .forms import ConsultaForm

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

def render_error(request, error_message):
    """
    Renderiza la página de consulta con un mensaje de error.
    """
    return render(request, 'hidroweb/consultar.html', {
        'error': error_message,
        'empresas': Empresa.objects.filter(activo=True),
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
    })

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
    return cursor.fetchall()  # Asegúrate de que esto devuelva los resultados correctamente



def consultar(request):
    empresas = Empresa.objects.filter(activo=True)
    error_message = None  # Inicializa el mensaje de error

    if request.method == 'GET':
        form = ConsultaForm()
        # Llenar las opciones del campo empresa_id
        form.fields['empresa_id'].choices += [(empresa.id, empresa.nombre) for empresa in empresas]
        return render(request, 'hidroweb/consultar.html', {
            'form': form,
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            'error_message': error_message,  # Pasa el mensaje de error a la plantilla
        })

    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        # Llenar las opciones del campo empresa_id
        form.fields['empresa_id'].choices += [(empresa.id, empresa.nombre) for empresa in empresas]

        if form.is_valid():
            recaptcha_response = request.POST.get('g-recaptcha-response')
            if not recaptcha_response or not validar_recaptcha(recaptcha_response):
                error_message = 'Error en la validación de reCAPTCHA.'
            else:
                empresa_id = form.cleaned_data['empresa_id']
                documento = form.cleaned_data['documento']
                tipo_consulta = form.cleaned_data['tipo_consulta']

                empresa = get_object_or_404(Empresa, id=empresa_id, activo=True)
                configurar_conexion_dinamica(empresa)

                try:
                    with connections[empresa.nombre].cursor() as cursor:
                        resultado = ejecutar_consulta(cursor, tipo_consulta, documento)

                        if resultado:
                            # Procesar resultados
                            datos_finales = [{
                                'numero_contrato': row[0],
                                'cedula': row[8],
                                'nombrecompleto': f"{row[4]} {row[5]} {row[6]}",
                                'situacion': row[1],
                                'fechasituacion': row[2],
                                'deudatotal': row[9],
                            } for row in resultado if row[0] is not None and row[8] is not None]

                            paginator = Paginator(datos_finales, 10)
                            page_number = request.GET.get('page')
                            page_obj = paginator.get_page(page_number)

                            return render(request, 'hidroweb/resultados.html', {
                                'page_obj': page_obj,
                                'empresa': empresa,
                                'documento': documento,
                                'tipo_consulta': tipo_consulta,
                            })
                        else:
                            error_message = "No se encontraron resultados verifica tu R.I.F/C.I o N.IC."
                except DatabaseError as e:
                    print(f"[ERROR] Error en la consulta SQL: Empresa: {empresa.nombre}, Error: {str(e)}")
                    error_message = "Error en la consulta: intente más tarde."
                except Exception as e:
                    print(f"[ERROR] Error inesperado: Empresa: {empresa.nombre}, Error: {str(e)}")
                    error_message = "Error inesperado: intente más tarde."
        else:
            error_message = 'Por favor, corrige los errores en el formulario.'

    return render(request, 'hidroweb/consultar.html', {
        'form': form,
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
        'error_message': error_message,  # Pasa el mensaje de error a la plantilla
    })
    
    

def error_404(request, exception):
    return render(request, 'layo404.html', status=404)

def error_403(request, exception):
    return render(request, '403.html', status=403)

def error_500(request):
    return render(request, '500.html', status=500)