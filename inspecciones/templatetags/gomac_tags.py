from django import template
from django.urls import reverse

from inspecciones.models import CriticidadNumerica, Respuesta

register = template.Library()


@register.simple_tag(takes_context=True)
def abs_url(context, view_name, *args, **kwargs):
    # Could add except for KeyError, if rendering the template
    # without a request available.
    return context['request'].build_absolute_uri(
        reverse(view_name, args=args, kwargs=kwargs)
    )


@register.filter
def as_abs_url(path, request):
    return request.build_absolute_uri(path)


@register.simple_tag(takes_context=True)
def get_filtro(context, filtro):
    if filtro == 'pendientes':
        respuestas = context['respuestas'].filter(criticidad_calculada_con_reparaciones__gt=0)
    elif filtro == 'reparadas':
        respuestas = context['respuestas'].filter(reparado=True)
    elif filtro == 'sinNovedad':
        respuestas = context['respuestas'].filter(criticidad_calculada=0)

    return respuestas


@register.simple_tag(takes_context=True)
def get_subRespuestas(context, respObject, filtro ):
    tipoDeRespuesta = respObject.tipo_de_respuesta
    print(tipoDeRespuesta)
    if tipoDeRespuesta == Respuesta.TiposDeRespuesta.seleccion_multiple:
        subRespuestas = context['respuestasMultiples'].filter(respuesta_multiple__id=respObject.id).order_by(
            '-criticidad_calculada_con_reparaciones')
        return {'subRespuestas': subRespuestas}
    elif tipoDeRespuesta in [Respuesta.TiposDeRespuesta.seleccion_unica, Respuesta.TiposDeRespuesta.numerica]:
        if respObject.respuesta_cuadricula is None:
            print('unica')
            subRespuestas = context['inspeccion'].respuestas.filter(id=respObject.id)
        else:
            print('de cuadricula')
            subRespuestas = [respObject]
        return {'subRespuestas': subRespuestas}


@register.simple_tag()
def get_respuesta(respObject):
    tipoDeRespuesta = respObject.tipo_de_respuesta
    opcion = ''
    criticidad = 0
    if tipoDeRespuesta == 'seleccion_unica':
        opcion = respObject.opcion_seleccionada
        criticidad = respObject.opcion_seleccionada.criticidad
    elif tipoDeRespuesta == 'parte_de_seleccion_multiple':
        opcion = respObject.opcion_respondida
        criticidad = respObject.opcion_respondida.criticidad
    elif tipoDeRespuesta == 'numerica':
        opcion = respObject.valor_numerico
        try:
            critiNumerica = CriticidadNumerica.objects.get(pregunta__id=respObject.pregunta_id,
                                                           valor_minimo__lte=opcion,
                                                           valor_maximo__gte=opcion)
            criticidad = critiNumerica.criticidad
        except CriticidadNumerica.DoesNotExist:
            criticidad = 0
    return {'opcion': opcion, 'criticidad': criticidad}
