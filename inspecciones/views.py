from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Avg, Count
from django.http import HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View

from inspecciones.forms import PerfilForm, UserForm, UserEditForm, PerfilEditForm
from inspecciones.models import Organizacion, Inspeccion, Perfil, Activo, Respuesta


class OrganizacionListView(LoginRequiredMixin, ListView):
    model = Organizacion


class OrganizacionDetailView(LoginRequiredMixin, DetailView):
    model = Organizacion

    def get_context_data(self, **kwargs):
        inspecciones = Inspeccion.objects.filter(
            cuestionario__organizacion=self.request.user.perfil.organizacion)
        """Agrega todas las caracteristicas."""
        context = {'caracteristicas': Organizacion.Caracteristicas.values,
                   'inspecciones': {
                       'total': inspecciones.count(),
                       'sinNovedad': inspecciones.filter(criticidad_calculada=0).count(),
                       'atrasadas': 10,
                       'promedio': inspecciones.aggregate(Avg('criticidad_calculada'))
                   }}
        context.update(kwargs)
        return super().get_context_data(**context)


class MiOrganizacionView(OrganizacionDetailView):
    def get_object(self, queryset=None):
        self.kwargs[self.pk_url_kwarg] = self.request.user.perfil.organizacion.pk
        return super().get_object(queryset)


class OrganizacionCreateView(LoginRequiredMixin, CreateView):
    model = Organizacion
    fields = ['nombre', 'logo', 'link', 'acerca', 'caracteristicas']


class OrganizacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Organizacion
    fields = ['nombre', 'logo', 'link', 'acerca', 'caracteristicas']


class OrganizacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Organizacion
    success_url = reverse_lazy('organizacion-list')


class UsuarioDetailView(LoginRequiredMixin, DetailView):
    model = Perfil


class UsuarioUpdateView(LoginRequiredMixin, TemplateResponseMixin, ContextMixin, View):
    """adaptado de https://stackoverflow.com/a/65847099/5076677"""

    template_name = "inspecciones/usuario_form.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        perfil = Perfil.objects.get(pk=self.kwargs['pk'])
        context["form_user"] = UserEditForm(prefix="user_form", instance=perfil.user)
        context["form_perfil"] = PerfilEditForm(prefix="perfil_form", instance=perfil)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        perfil = Perfil.objects.get(pk=self.kwargs['pk'])
        # Process forms
        form_user = UserEditForm(request.POST, prefix="user_form", instance=perfil.user)
        form_perfil = PerfilEditForm(request.POST, prefix="perfil_form", instance=perfil)
        if form_user.is_valid() and form_perfil.is_valid():
            # Save user
            form_user.save()
            # Save profile
            form_perfil.save()
            # Redirect to success page
            return HttpResponseRedirect(reverse("mi-organizacion"))
        else:
            # overwrite context data for this form so that it is   \
            # returned to the page with validation errors
            context["form_user"] = form_user
            context["form_perfil"] = form_perfil

        # Pass context back to render_to_response() including any invalid forms
        return self.render_to_response(context)


class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Perfil
    success_url = reverse_lazy('mi-organizacion')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.user.delete()
        return HttpResponseRedirect(success_url)


class RegistrationView(TemplateResponseMixin, ContextMixin, View):
    """adaptado de https://stackoverflow.com/a/65847099/5076677"""

    template_name = "django_registration/registration_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add blank forms to context with prefixes
        context["form_user"] = UserForm(prefix="user_form")
        context["form_perfil"] = PerfilForm(prefix="perfil_form")
        return context

    def get(self, request, *args, **kwargs):
        if "org" not in self.request.GET:
            return HttpResponseBadRequest(b'No organizacion_id provided.')

        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        try:
            organizacion_id = self.request.GET["org"]
        except MultiValueDictKeyError:
            return HttpResponseBadRequest(b'No organizacion_id provided.')
        context = self.get_context_data()
        # Process forms
        form_user = UserForm(request.POST, prefix="user_form")
        form_perfil = PerfilForm(request.POST, prefix="perfil_form")
        if form_user.is_valid() and form_perfil.is_valid():
            # Save user
            new_user = form_user.save(commit=False)
            new_user.first_name = form_user.cleaned_data["nombre"]
            new_user.last_name = form_user.cleaned_data["apellido"]
            new_user.save()
            # Save profile
            new_perfil = form_perfil.save(commit=False)
            new_perfil.user = new_user
            new_perfil.organizacion = Organizacion.objects.get(pk=organizacion_id)
            new_perfil.rol = Perfil.Roles.inspector
            new_perfil.save()
            # Redirect to success page
            return HttpResponseRedirect(reverse("login"))
        else:
            # overwrite context data for this form so that it is   \
            # returned to the page with validation errors
            context["form_user"] = form_user
            context["form_perfil"] = form_perfil

        # Pass context back to render_to_response() including any invalid forms
        return self.render_to_response(context)


class InspeccionListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        return Inspeccion.objects.filter(cuestionario__organizacion=self.request.user.perfil.organizacion) \
            .order_by('-momento_inicio')



class InspeccionDetailView(LoginRequiredMixin, DetailView):
    model = Inspeccion
    pk_url_kwarg = 'inspeccion_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Son las que tienen inspeccionId no nula, de tipo seleccion multiple, seleccion unica
        # cuadricula y numerica
        respuestas = context['inspeccion'].respuestas.all().order_by('-criticidad_calculada_con_reparaciones')
        idsRespuestas = context['inspeccion'].respuestas.values_list('id', flat=True)
        # Son las respuestas padre de cada pregunta de la cuadricula
        respuestasCuadricula = Respuesta.objects.filter(respuesta_cuadricula__id__in=idsRespuestas)
        respuestasCuadriculaIds = respuestasCuadricula.values_list('id', flat=True)
        # Incluye las subrespuestas de las preguntas cuadricula multiple y de seleccion multiple
        respuestasMultiples = Respuesta.objects.filter(
            Q(respuesta_multiple__id__in=idsRespuestas) | Q(respuesta_multiple__id__in=respuestasCuadriculaIds),
            opcion_respondida_esta_seleccionada=True)
        context.update({'respuestasMultiples': respuestasMultiples})
        # Aqui se excluyen las respuestas generales de las preguntas tipo cuadricula.
        respuestas = respuestas.exclude(tipo_de_respuesta='cuadricula') | respuestasCuadricula
        context.update({'respuestas': respuestas})
        reparadas = respuestas.filter(reparado=True).count()
        pendientes = respuestas.filter(
            criticidad_calculada_con_reparaciones__gt=0).count()
        sinNovedad = respuestas.filter(
            criticidad_calculada=0).count()
        context.update({'grupos': {'reparadas': reparadas, 'pendiente': pendientes, 'sinNovedad': sinNovedad,
                                   'todas': reparadas + pendientes + sinNovedad}})
        return context


class ActivoListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        activos = Activo.objects.filter(organizacion=self.request.user.perfil.organizacion)
        print(activos)
        return activos


def get_chart_template(graphType, data, title, titleSize='16px'):
    return {
        'chart': {'type': graphType,
                  'borderColor': '#ffffff',
                  'plotBackgroundColor': None,
                  'plotBorderWidth': None,
                  'plotShadow': False,
                  'height': '300px',
                  },
        'title': {'text': title,
                  'style': {
                      "fontSize": titleSize
                  },
                  },
        'accessibility': {
            'point': {
                'valueSuffix': '%'
            }
        },
        'plotOptions': {
            'pie': {
                'allowPointSelect': True,
                'cursor': 'pointer',
                'dataLabels': {
                    'enabled': True,
                    'format': '<b>{point.name}</b>: {point.percentage:.1f} %'
                },
            },

        },
        'series': [data]
    }


def get_sub_respuesta(resp):
    sub = resp.sub_respuestas()
    return sub


def chart_data_state(request):
    dataset = Inspeccion.objects.filter(cuestionario__organizacion=request.user.perfil.organizacion)
    ids = dataset.values_list('id', flat=True)
    respuestas = Respuesta.objects.filter(inspeccion__id__in=ids, criticidad_calculada__lte=4)
    idsRespPadres = respuestas.values_list('id', flat=True)
    subRespMultiples = Respuesta.objects.filter(respuesta_multiple__id__in=idsRespPadres)
    unicas = respuestas.filter(tipo_de_respuesta__in=['seleccion_unica', 'numerica'])
    subRespCuadricula = Respuesta.objects.filter(respuesta_cuadricula__id__in=idsRespPadres,
                                                 tipo_de_respuesta__in=['seleccion_unica', 'numerica'])
    subResp = subRespMultiples | unicas | subRespCuadricula
    respuestasCriticas = subResp.values('criticidad_calculada').annotate(cantidad=Count('criticidad_calculada'))
    novedades = subResp.filter(criticidad_calculada__gt=0).count()
    reparadas = subResp.filter(reparado=True).count()
    dataState = {
        'name': 'Cantidad',
        'data': [{
            "name": 'En reparación',
            "y": dataset.filter(estado='en_reparacion').count()
        },
            {
                "name": 'Borrador',
                "y": dataset.filter(estado='borrador').count()
            },
            {
                "name": 'Finalizada',
                "y": dataset.filter(estado='finalizada').count()
            }
        ]
    }

    dataReparaciones = {
        'name': 'Cantidad',
        'data': [{
            "name": 'Pendientes',
            "y": novedades - reparadas
        },
            {
                "name": 'Atendidas',
                "y": reparadas
            },
        ]
    }
    dataCriticidad = {
        'name': "Cantidad",
        'colorByPoint': True,
        'data': list(map(lambda x: {'name': x['criticidad_calculada'], 'y': x['cantidad']}, respuestasCriticas))
    }
    chartState = get_chart_template('pie', dataState, 'Estado de inspecciones')
    chartReparaciones = get_chart_template('pie', dataReparaciones, 'Novedades pendientes vs novedades atendidas',
                                           "14px")
    chartCriticidad = get_chart_template('column', dataCriticidad,
                                         'Comportamiento de criticidad en las respuestas seleccionadas', '14px')
    chartCriticidad['xAxis'] = {
        'title': {
            'text': 'Criticidad'
        },
        'categories': list(map(lambda x: x['criticidad_calculada'], respuestasCriticas))
    }
    chartCriticidad['legend'] = {
        'enabled': False
    }
    chartCriticidad['yAxis'] = {
        'title': {
            'text': 'Total de respuestas'
        }
    }
    chartReparaciones['subtitle'] = {
        'text': '<div>Novedades<span class="ms-1 badge rounded-pill bg-danger">' + str(
            novedades) + '</span></div>' + '</span>' + '<br>' + '<div>Reparadas<span class="badge ms-1 rounded-pill bg-warning text-dark">' + str(
            reparadas) + '</span></div>' + '</span>',
        'useHTML': True,
        'align': 'left',
        'verticalAlign': 'middle',
    }
    chartReparaciones['chart']['marginRight'] = -50
    chartReparaciones['chart']['marginTop'] = 50

    return JsonResponse([chartState, chartCriticidad, chartReparaciones], safe=False)
