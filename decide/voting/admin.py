from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import QuestionOption
from base.models import Auth
from .models import Question
from .models import Voting
from .models import Candidatura
from .filters import StartedFilter
from authentication.models import VotingUser


def start(modeladmin, request, queryset):
    for v in queryset.all():
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()


def stop(ModelAdmin, request, queryset):
    for v in queryset.all():
        v.end_date = timezone.now()
        v.save()

def realizarEleccionesPrimarias(ModelAdmin, request, queryset):
    
    for c in queryset.all():
        q1 = Question(desc='elige representante de primero de la candidatura "'+ c.nombre+'"')
        q1.save()
        i=1
        from authentication.models import VotingUser
        usuarios_candidatura = VotingUser.objects.filter(candidatura=c)
        for usr in usuarios_candidatura.filter(curso="PRIMERO"):
            qo = QuestionOption(question = q1, number=i, option=usr.user.first_name+" "+usr.user.last_name)
            qo.save()
            i+=1
        q2 = Question(desc='elige representante de segundo de la candidatura "'+c.nombre+'"')
        q2.save()
        i=1
        usuarios_candidatura = VotingUser.objects.filter(candidatura=c)
        for usr in usuarios_candidatura.filter(curso="SEGUNDO"):
            qo = QuestionOption(question = q2, number=i, option=usr.user.first_name+" "+usr.user.last_name)
            qo.save()
            i+=1
        q3 = Question(desc='elige representante de tercero de la candidatura "'+ c.nombre+'"')
        q3.save()
        i=1
        usuarios_candidatura = VotingUser.objects.filter(candidatura=c)
        for usr in usuarios_candidatura.filter(curso="TERCERO"):
            qo = QuestionOption(question = q3, number=i, option=usr.user.first_name+" "+usr.user.last_name)
            qo.save()
            i+=1
        q4 = Question(desc='elige representante de cuarto de la candidatura "'+ c.nombre+'"')
        q4.save()
        i=1
        usuarios_candidatura = VotingUser.objects.filter(candidatura=c)
        for usr in usuarios_candidatura.filter(curso="CUARTO"):
            qo = QuestionOption(question = q4, number=i, option=usr.user.first_name+" "+usr.user.last_name)
            qo.save()
            i+=1
        q5 = Question(desc='elige representante de máster de la candidatura "'+ c.nombre+'"')
        q5.save()
        i=1
        usuarios_candidatura = VotingUser.objects.filter(candidatura=c)
        for usr in usuarios_candidatura.filter(curso="MASTER"):
            qo = QuestionOption(question = q5, number=i, option=usr.user.first_name+" "+usr.user.last_name)
            qo.save()
            i+=1
        voting = Voting(name='Votaciones de la candidatura "'+c.nombre+'"',desc="Elige a los representantes de tu candidatura."
        , tipo="Primary voting", candiancy=c)
        voting.save()

        voting.question.add(q1, q2, q3, q4, q5)

        #No sé si habrá que filtrarlos de alguna manera.
        for auth in Auth.objects.all():
            voting.auths.add(auth)
        messages.add_message(request, messages.SUCCESS, "¡Las elecciones primarias se han creado!")


realizarEleccionesPrimarias.short_description="Realizar las votaciones primarias de candidaturas seleccionadas"

def realizarEleccionGeneral(ModelAdmin, request, queryset):
    numero_votaciones_generales = Voting.objects.filter(tipo='General voting').count()
    indice_votacion = str(numero_votaciones_generales + 1)
    q1 = Question(desc='Votación general ' + indice_votacion + ': Elige al delegado de primero')
    q1.save()
    q2 = Question(desc='Votación general ' + indice_votacion + ': Elige al delegado de segundo')
    q2.save()
    q3 = Question(desc='Votación general ' + indice_votacion + ': Elige al delegado de tercero')
    q3.save()
    q4 = Question(desc='Votación general ' + indice_votacion + ': Elige al delegado de cuarto')
    q4.save()
    q5 = Question(desc='Votación general ' + indice_votacion + ': Elige al delegado del master')
    q5.save()
    q6 = Question(desc='Votación general ' + indice_votacion + ': Elige al delegado al centro')
    q6.save()
    q7 = Question(desc='Votación general ' + indice_votacion + ': Elige a los miembros de delegación de alumnos')
    q7.save()
    try:
        contador = 1
        for c in queryset.all():
            nombreCand = c.nombre
            qo1 = QuestionOption(question=q1, number=contador, option='Candidatura "' + nombreCand + '": ' + c.representanteDelegadoPrimero.first_name
                                    + ' ' + c.representanteDelegadoPrimero.last_name)
            qo1.save()
            qo2 = QuestionOption(question=q2, number=contador, option='Candidatura "' + nombreCand + '": ' + c.representanteDelegadoSegundo.first_name
                                    + ' ' + c.representanteDelegadoSegundo.last_name)
            qo2.save()
            qo3 = QuestionOption(question=q3, number=contador, option='Candidatura "' + nombreCand + '": ' + c.representanteDelegadoTercero.first_name
                                    + ' ' + c.representanteDelegadoTercero.last_name)
            qo3.save()
            qo4 = QuestionOption(question=q4, number=contador, option='Candidatura "' + nombreCand +   '": ' + c.representanteDelegadoCuarto.first_name
                                    + ' ' + c.representanteDelegadoCuarto.last_name)
            qo4.save()
            qo5 = QuestionOption(question=q5, number=contador, option='Candidatura "' + nombreCand + '": ' + c.representanteDelegadoMaster.first_name
                                    + ' ' + c.representanteDelegadoMaster.last_name)
            qo5.save()
            qo6 = QuestionOption(question=q6, number=contador, option='Candidatura "' + nombreCand + '": ' + c.delegadoCentro.first_name
                                    + ' ' + c.delegadoCentro.last_name)
            qo6.save()
            #Para delegacion de alumno hay que poner una opcion por cada alumno de la candidatura que no se presente a ninguno de los cargos previos
            alumnos_candidatura_sin_cargo = VotingUser.objects.filter(candidatura=c)
            i = 0
            for alumno in alumnos_candidatura_sin_cargo:
                if (alumno.user!=c.representanteDelegadoPrimero and alumno!=c.representanteDelegadoSegundo and alumno!=c.representanteDelegadoTercero and alumno!=c.representanteDelegadoCuarto and alumno!=c.representanteDelegadoMaster and alumno!=c.delegadoCentro):
                    qo7 = QuestionOption(question=q7, number=(contador+i), option='Candidatura "' + nombreCand + '": ' + alumno.user.first_name
                                    + ' ' + alumno.user.last_name)
                    qo7.save()
                    i+=1
            contador += 1
        
        votacion = Voting(name='Votación general ' + indice_votacion, desc='Elige a los representantes de tu centro', tipo='General voting')
        votacion.save()
        votacion.question.add(q1, q2, q3, q4, q5, q6, q7)

        # Echarle un vistazo
        for auth in Auth.objects.all():
            votacion.auths.add(auth)
        messages.add_message(request, messages.SUCCESS, "¡La elección general se ha creado!")
    except:
        # En el caso de que haya alguna candidatura que no ha celebrado primarias, borramos las prunguntas pues no se creara la votacion general
        q1.delete()
        q2.delete()
        q3.delete()
        q4.delete()
        q5.delete()
        q6.delete()
        q7.delete()
        messages.add_message(request, messages.ERROR, 'Se ha seleccionado alguna candidatura que no había celebrado votaciones primarias para elegir a los representantes')
realizarEleccionGeneral.short_description='Crear votación general con las candidaturas seleccionadas'


def tally(ModelAdmin, request, queryset):
    for v in queryset.filter(end_date__lt=timezone.now()):
        token = request.session.get('auth-token', '')
        v.tally_votes(token)

def borrarVotingPrimary(ModelAdmin, request, queryset):
    opciones=["primero","segundo","tercero","cuarto","máster"]
    for c in queryset.all():
        for voting in Voting.objects.filter(candiancy=c):
            voting.delete()
        for opcion in opciones:
            for question in Question.objects.filter(desc__regex='elige representante de '+ opcion+' de la candidatura "'+c.nombre+'"'):
                question.delete()
    messages.add_message(request, messages.SUCCESS, "¡Las elecciones primarias se han borrado!")
borrarVotingPrimary.short_description= "Borrar votación de la candidatura completa('Voting', 'Questions' y 'QuestionOptions')"

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]

class CandidaturaAdmin(admin.ModelAdmin):
    actions = [ realizarEleccionesPrimarias , borrarVotingPrimary, realizarEleccionGeneral]

class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', )

    actions = [ start, stop, tally ]


admin.site.register(Voting, VotingAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Candidatura, CandidaturaAdmin)
