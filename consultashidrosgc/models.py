from django.db import models

class Empresa(models.Model):
    nombre = models.CharField('Nombre Empresa:',max_length=100, unique=True)
    host = models.CharField('IP Host:',max_length=100)
    puerto = models.CharField('Puerto de Conexion:',max_length=4, default=5432)
    nombre_db = models.CharField('Nombre DataBase:',max_length=100, default="HIDROSGC")
    usuario = models.CharField('Nombre de Usuario:',max_length=100)
    contraseña = models.CharField('Contraseña:',max_length=128)  
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "hidrologicas"
        verbose_name_plural = "hidrologicas"
        db_table = "hidrologicas"



class ResultadoConsulta(models.Model):
    cedula = models.CharField(max_length=20, verbose_name="R.I.F o C.I")
    numero_contrato = models.CharField(max_length=100, verbose_name="Número de Contrato")    
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    situacion = models.CharField(max_length=100, verbose_name="Situación", blank=True, null=True)
    fechasituacion = models.DateField(verbose_name="Fecha de Situación", blank=True, null=True)
    deudatotal = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Deuda Total", blank=True, null=True)
    empresa = models.CharField(max_length=255, verbose_name="Empresa")
    empresa_id = models.IntegerField(verbose_name="ID de la Empresa")
    fecha_consulta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Consulta")

    def __str__(self):
        return f"{self.nombre_completo} - {self.numero_contrato}"

    class Meta:
        verbose_name = "Resultado de Consulta"
        verbose_name_plural = "Resultados de Consultas"