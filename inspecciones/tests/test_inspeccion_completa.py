import uuid

from django.urls import reverse
from rest_framework import status

from inspecciones.models import Inspeccion, OpcionDeRespuesta
from inspecciones.tests.test_classes import InspeccionesAuthenticatedTestCase


class InspeccionCompletaTest(InspeccionesAuthenticatedTestCase):
    """TODO: reducir duplicacion de codigo"""

    # funciones auxiliares

    def request_inspeccion_y_obtener_respuesta(self, id_inspeccion, id_cuestionario):
        url_obtener = reverse('api:inspeccion-completa-detail', args=[id_inspeccion])
        response = self.client.get(url_obtener)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inspeccion = response.data
        self.assertEqual(inspeccion['id'], str(id_inspeccion))
        self.assertEqual(inspeccion['cuestionario'], id_cuestionario)
        self.assertIsNotNone(inspeccion['momento_inicio'])
        self.assertEqual(inspeccion['activo'], self.activo.id)
        self.assertEqual(len(inspeccion['respuestas']), 1)
        respuesta = inspeccion['respuestas'][0]
        return respuesta

    def test_crear_inspeccion_para_cuestionario_vacio(self):
        response_cuestionario, id_cuestionario = self.crear_cuestionario(bloques=[])
        self.assertEqual(response_cuestionario.status_code, status.HTTP_201_CREATED)

        url = reverse('api:inspeccion-completa-list')
        id_inspeccion = uuid.uuid4()
        response = self.client.post(url, {'id': id_inspeccion, 'cuestionario': id_cuestionario,
                                          'momento_inicio': '2020-01-01T00:00:00Z', 'activo': self.activo.id,
                                          'estado': 'borrador', 'criticidad_calculada': 0,
                                          'criticidad_calculada_con_reparaciones': 0,
                                          },
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inspeccion.objects.count(), 1)

    def test_crear_inspeccion_para_cuestionario_con_una_pregunta_de_seleccion_unica(self):
        (response_cuestionario,
         id_cuestionario), id_pregunta, id_opcion = self.crear_cuestionario_con_pregunta_de_seleccion_unica()
        self.assertEqual(response_cuestionario.status_code, status.HTTP_201_CREATED)

        (response, id_inspeccion) = self.crear_inspeccion_con_respuesta_de_seleccion_unica(
            id_cuestionario, id_pregunta, id_opcion)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inspeccion.objects.count(), 1)
        inspeccion = Inspeccion.objects.get()
        self.assertEqual(inspeccion.respuestas.count(), 1)
        respuesta = inspeccion.respuestas.get()
        self.assertEqual(respuesta.opcion_seleccionada, OpcionDeRespuesta.objects.get(id=id_opcion))
        self.assertEqual(respuesta.reparado, False)
        self.assertEqual(respuesta.observacion, 'observacion')
        self.assertEqual(respuesta.observacion_reparacion, 'observacion reparacion')
        self.assertEqual(respuesta.momento_respuesta.isoformat(), '2020-01-01T00:00:00+00:00')
        self.assertEqual(respuesta.fotos_base.count(), 1)
        self.assertEqual(respuesta.fotos_reparacion.count(), 1)
        foto1 = respuesta.fotos_base.get()
        self.assertEqual(foto1.id, self.foto_inspeccion1.id)
        foto2 = respuesta.fotos_reparacion.get()
        self.assertEqual(foto2.id, self.foto_inspeccion2.id)

        respuesta = self.request_inspeccion_y_obtener_respuesta(id_inspeccion, id_cuestionario)
        self.assertEqual(len(respuesta['fotos_base_url']), 1)
        self.assertTrue(respuesta['fotos_base_url'][0]['foto'].startswith('http://testserver/media/fotos_inspecciones/'))
        self.assertEqual(len(respuesta['fotos_reparacion_url']), 1)
        self.assertTrue(respuesta['fotos_reparacion_url'][0]['foto'].startswith('http://testserver/media/fotos_inspecciones/'))
        self.assertEqual(respuesta['opcion_seleccionada'], id_opcion)
        self.assertFalse(respuesta['reparado'])

    def test_crear_inspeccion_para_cuestionario_con_una_pregunta_de_seleccion_multiple(self):
        (response_cuestionario,
         id_cuestionario), id_pregunta, id_opcion = self.crear_cuestionario_con_pregunta_de_seleccion_multiple()
        self.assertEqual(response_cuestionario.status_code, status.HTTP_201_CREATED)

        (response, id_inspeccion) = self.crear_inspeccion_con_respuesta_de_seleccion_multiple(
            id_cuestionario, id_pregunta, id_opcion)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inspeccion.objects.count(), 1)
        inspeccion = Inspeccion.objects.get()
        self.assertEqual(inspeccion.respuestas.count(), 1)
        respuesta = inspeccion.respuestas.get()
        self.assertEqual(respuesta.tipo_de_respuesta, 'seleccion_multiple')
        self.assertEqual(respuesta.subrespuestas_multiple.count(), 1)
        subrespuesta = respuesta.subrespuestas_multiple.get()
        self.assertEqual(subrespuesta.opcion_respondida.id, id_opcion)

        respuesta = self.request_inspeccion_y_obtener_respuesta(id_inspeccion, id_cuestionario)
        self.assertEqual(len(respuesta['subrespuestas_multiple']), 1)
        subrespuesta = respuesta['subrespuestas_multiple'][0]
        self.assertEqual(subrespuesta['opcion_respondida'], id_opcion)
        self.assertTrue(subrespuesta['opcion_respondida_esta_seleccionada'])

    def test_crear_inspeccion_para_cuestionario_con_una_pregunta_numerica(self):
        (response_cuestionario,
         id_cuestionario), id_pregunta, id_criticidad = self.crear_cuestionario_con_pregunta_numerica()
        self.assertEqual(response_cuestionario.status_code, status.HTTP_201_CREATED)

        (response, id_inspeccion) = self.crear_inspeccion_con_respuesta_numerica(
            id_cuestionario, id_pregunta)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inspeccion.objects.count(), 1)
        inspeccion = Inspeccion.objects.get()
        self.assertEqual(inspeccion.respuestas.count(), 1)
        respuesta = inspeccion.respuestas.get()
        self.assertEqual(respuesta.valor_numerico, 5)

        respuesta = self.request_inspeccion_y_obtener_respuesta(id_inspeccion, id_cuestionario)
        self.assertEqual(respuesta['valor_numerico'], 5)

    def test_crear_inspeccion_para_cuestionario_con_una_pregunta_de_cuadricula(self):
        (response_cuestionario,
         id_cuestionario), id_pregunta, id_opcion, id_subpregunta = self.crear_cuestionario_con_pregunta_de_cuadricula()
        self.assertEqual(response_cuestionario.status_code, status.HTTP_201_CREATED)

        (response, id_inspeccion) = self.crear_inspeccion_con_respuesta_de_cuadricula(
            id_cuestionario, id_pregunta, id_opcion, id_subpregunta)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inspeccion.objects.count(), 1)
        inspeccion = Inspeccion.objects.get()
        self.assertEqual(inspeccion.respuestas.count(), 1)
        respuesta = inspeccion.respuestas.get()
        self.assertEqual(respuesta.tipo_de_respuesta, 'cuadricula')
        self.assertEqual(respuesta.subrespuestas_cuadricula.count(), 1)
        subrespuesta = respuesta.subrespuestas_cuadricula.get()
        self.assertEqual(subrespuesta.opcion_seleccionada.id, id_opcion)

        respuesta = self.request_inspeccion_y_obtener_respuesta(id_inspeccion, id_cuestionario)
        self.assertEqual(len(respuesta['subrespuestas_cuadricula']), 1)
        subrespuesta = respuesta['subrespuestas_cuadricula'][0]
        self.assertEqual(subrespuesta['opcion_seleccionada'], id_opcion)
