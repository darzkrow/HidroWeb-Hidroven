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

    # Manejo de la solicitud GET
    if request.method == 'GET':
        form = ConsultaForm()
        form.fields['empresa_id'].choices += [(empresa.id, empresa.nombre) for empresa in empresas]  # Llenar opciones
        return render(request, 'hidroweb/consultar.html', {
            'form': form,
            'empresas': empresas,
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
        })

    # Manejo de la solicitud POST
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        form.fields['empresa_id'].choices = [(empresa.id, empresa.nombre) for empresa in empresas]  # Llenar opciones

        if form.is_valid():
            recaptcha_response = request.POST.get('g-recaptcha-response')
            if not recaptcha_response or not validar_recaptcha(recaptcha_response):
                return render_error(request, 'Error en la validación de reCAPTCHA.')

            empresa_id = form.cleaned_data['empresa_id']
            documento = form.cleaned_data['documento']
            tipo_consulta = form.cleaned_data['tipo_consulta']

            empresa = get_object_or_404(Empresa, id=empresa_id, activo=True)
            configurar_conexion_dinamica(empresa)

            try:
                with connections[empresa.nombre].cursor() as cursor:
                    resultado = ejecutar_consulta(cursor, tipo_consulta, documento)

                    # Asegúrate de que resultado no sea None
                    if resultado:
                        columnas = [column[0] for column in cursor.description]

                        # Construye datos_finales
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
                        return render_error(request, "No se encontraron resultados para la consulta.")
            except DatabaseError as e:
                print(f"[ERROR] Error en la consulta SQL: Empresa: {empresa.nombre}, Error: {str(e)}")
                return render_error(request, "Error en la consulta: intente más tarde.")
            except Exception as e:
                print(f"[ERROR] Error inesperado: Empresa: {empresa.nombre}, Error: {str(e)}")
                return render_error(request, "Error inesperado: intente más tarde.")
        else:
            # Si el formulario no es válido, renderiza de nuevo con errores
            return render(request, 'hidroweb/consultar.html', {
                'form': form,
                'empresas': empresas,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            })