# check_empresas.py
from django.core.management.base import BaseCommand
from consultashidrosgc.models import ResultadoConsulta, Empresa
import socket

class Command(BaseCommand):
    help = 'Verifica el estado de las empresas asociadas a los resultados de consulta'

    def handle(self, *args, **kwargs):
        resultados = ResultadoConsulta.objects.all()
        empresas_inactivas = []

        for resultado in resultados:
            try:
                # Intenta resolver la dirección IP de la empresa
                empresa = Empresa.objects.get(id=resultado.empresa_id)
                socket.gethostbyaddr(empresa.host)  # Verifica si la IP es activa
                self.stdout.write(self.style.SUCCESS(f'La IP {empresa.host} de {empresa.nombre} está activa.'))
            except (socket.herror, Empresa.DoesNotExist):
                # Si no se puede resolver o la empresa no existe, se cambia el estado a False
                empresas_inactivas.append(resultado.empresa_id)
                self.stdout.write(self.style.WARNING(f'La IP {empresa.host} de {empresa.nombre} no está activa. Cambiando a inactiva.'))
                empresa.activo = False
                empresa.save()

        if empresas_inactivas:
            self.stdout.write(self.style.ERROR(f'Se encontraron empresas inactivas: {empresas_inactivas}'))
        else:
            self.stdout.write(self.style.SUCCESS('Todas las empresas están activas.'))