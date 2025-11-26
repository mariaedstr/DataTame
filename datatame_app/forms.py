#from allauth.account.forms import SignupForm
from django import forms
from .models import LutaRegistrada, Atleta, Luta

class LutaForm(forms.ModelForm):
    class Meta:
        model = Luta
        fields = [
            'atleta',
            'adversario',
            'golpes_atleta',
            'golpes_adversario',
            'vantagem_atleta',
            'vantagem_adversario',
            'penalidade_atleta',
            'penalidade_adversario',
            'resultado',
        ]


class LutaRegistradaForm(forms.ModelForm):
    adversario = forms.CharField(
        required=False,
        label='Nome do adversário',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = LutaRegistrada
        exclude = ('criado_em',)
        widgets = {
            # básicos
            'tempo_luta_segundos': forms.NumberInput(attrs={'class':'form-control'}),
            'shidos_atleta': forms.NumberInput(attrs={'class':'form-control'}),
            'shidos_oponente': forms.NumberInput(attrs={'class':'form-control'}),
            'numero_pausas': forms.NumberInput(attrs={'class':'form-control'}),
            'ippon_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'ippon_op': forms.NumberInput(attrs={'class':'form-control'}),
            'wazari_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'wazari_op': forms.NumberInput(attrs={'class':'form-control'}),
            'yuko_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'yuko_op': forms.NumberInput(attrs={'class':'form-control'}),
            
            # newaza
            'newaza_tentativas_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'newaza_tentativas_op': forms.NumberInput(attrs={'class':'form-control'}),
            'newaza_acertos_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'newaza_acertos_op': forms.NumberInput(attrs={'class':'form-control'}),

            # tewaza
            'tewaza_tentativas_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'tewaza_tentativas_op': forms.NumberInput(attrs={'class':'form-control'}),
            'tewaza_acertos_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'tewaza_acertos_op': forms.NumberInput(attrs={'class':'form-control'}),

            # koshiwaza
            'koshiwaza_tentativas_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'koshiwaza_tentativas_op': forms.NumberInput(attrs={'class':'form-control'}),
            'koshiwaza_acertos_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'koshiwaza_acertos_op': forms.NumberInput(attrs={'class':'form-control'}),

            # ashiwaza
            'ashiwaza_tentativas_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'ashiwaza_tentativas_op': forms.NumberInput(attrs={'class':'form-control'}),
            'ashiwaza_acertos_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'ashiwaza_acertos_op': forms.NumberInput(attrs={'class':'form-control'}),

            # sutemiwaza
            'sutemiwaza_tentativas_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'sutemiwaza_tentativas_op': forms.NumberInput(attrs={'class':'form-control'}),
            'sutemiwaza_acertos_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'sutemiwaza_acertos_op': forms.NumberInput(attrs={'class':'form-control'}),

            # iniciativa
            'iniciativa_pegada_atl': forms.NumberInput(attrs={'class':'form-control'}),
            'iniciativa_pegada_op': forms.NumberInput(attrs={'class':'form-control'}),

            # resultado
            'resultado': forms.Select(
                choices=[(1, 'Vitória'), (0, 'Derrota')],
                attrs={'class': 'form-select'}
            ),
        }

    def __init__(self, *args, **kwargs):
        equipe = kwargs.pop('equipe', None)
        super().__init__(*args, **kwargs)

        # atleta virá da view
        self.fields['atleta'].queryset = Atleta.objects.none()

        # garante que todo input tem class form-control
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs.setdefault('class', 'form-control')
