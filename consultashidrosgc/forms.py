# forms.py
from django import forms

class ConsultaForm(forms.Form):
    empresa_id = forms.ChoiceField(
        label='Hidrológica',
        choices=[
             ('', 'Selecciona'),],
        initial='',# Se llenará dinámicamente en la vista
        required=True,
             widget=forms.Select(attrs={'': 'disabled'}) 
    )

    tipo_consulta = forms.ChoiceField(
        label='Tipo de Consulta',
        choices=[
             ('', 'Selecciona'),
            ('cedula', 'Cédula/RIF'),
            ('nic', 'NIC')
        ],
        initial='',
        required=True
    )
    documento = forms.CharField(
        label='R.I.F/C.I o N.I.C',
        max_length=10,  # Limitar a 20 caracteres
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese R.I.F/C.I o N.I.C'})
    )