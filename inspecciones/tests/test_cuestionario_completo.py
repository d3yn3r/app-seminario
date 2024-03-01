import uuid

from django.urls import reverse
from rest_framework import status

from inspecciones.models import Cuestionario, Bloque, Pregunta, OpcionDeRespuesta
from inspecciones.tests.test_classes import InspeccionesAuthenticatedTestCase


class CuestionarioCompletoTest(InspeccionesAuthenticatedTestCase):
    # funciones auxiliares

    def request_cuestionario_y_obtener_bloque(self, id_cuestionario):
        url_obtener = reverse('api:cuestionario-completo-detail', args=[id_cuestionario])
        response = self.client.get(url_obtener)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cuestionario = response.data
        self.assertEqual(cuestionario['id'], str(id_cuestionario))
        self.assertEqual(cuestionario['version'], 1)
        self.assertEqual(cuestionario['tipo_de_inspeccion'], 'preoperacional')
        self.assertEqual(cuestionario['periodicidad_dias'], 1)
        self.assertEqual(len(cuestionario['bloques']), 1)
        bloque = cuestionario['bloques'][0]
        self.assertEqual(bloque['n_orden'], 1)
        return bloque

    # inicio tests

    def test_crear_cuestionario_con_bloque(self):
        url = reverse('api:cuestionario-completo-list')
        response = self.client.post(url, {'id': uuid.uuid4(), 'tipo_de_inspeccion': 'preoperacional', 'version': 1,
                                          'estado': 'finalizado',
                                          'periodicidad_dias': 1, 'etiquetas_aplicables': [],
                                          'bloques': [
                                              {'id': uuid.uuid4(), 'n_orden': 1}
                                          ]},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cuestionario.objects.count(), 1)
        cuestionario = Cuestionario.objects.get()
        self.assertEqual(cuestionario.bloques.count(), 1)

    def test_crear_cuestionario_con_etiquetas(self):
        url = reverse('api:cuestionario-completo-list')
        response = self.client.post(url, {'id': uuid.uuid4(), 'tipo_de_inspeccion': 'preoperacional', 'version': 1,
                                          'estado': 'finalizado',
                                          'periodicidad_dias': 1,
                                          'etiquetas_aplicables': [{'clave': 'color', 'valor': 'amarillo'}],
                                          'bloques': []},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cuestionario.objects.count(), 1)
        cuestionario = Cuestionario.objects.get()
        self.assertEqual(cuestionario.etiquetas_aplicables.count(), 1)
        etiqueta = cuestionario.etiquetas_aplicables.get()
        self.assertEqual(etiqueta.clave, 'color')
        self.assertEqual(etiqueta.valor, 'amarillo')

    def test_crear_cuestionario_con_bloque_y_titulo(self):
        url = reverse('api:cuestionario-completo-list')
        response = self.client.post(url, {'id': uuid.uuid4(), 'tipo_de_inspeccion': 'preoperacional', 'version': 1,
                                          'periodicidad_dias': 1, 'etiquetas_aplicables': [], 'estado': 'finalizado',
                                          'bloques': [
                                              {'id': uuid.uuid4(), 'n_orden': 1,
                                               'titulo': {'id': uuid.uuid4(), 'titulo': 'tit', 'descripcion': 'desc'}
                                               }
                                          ]},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cuestionario.objects.count(), 1)
        cuestionario = Cuestionario.objects.get()
        self.assertEqual(cuestionario.bloques.count(), 1)
        bloque = cuestionario.bloques.get()
        self.assertIsNotNone(bloque.titulo)

    def test_crear_cuestionario_con_bloque_y_titulo_y_foto(self):
        foto_id = self.foto_cuestionario.id
        id_titulo = uuid.uuid4()
        response, id_cuestionario = self.crear_cuestionario_con_bloque(
            titulo={'id': id_titulo, 'titulo': 'tit', 'descripcion': 'desc', 'fotos': [foto_id], })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # probar que la informacion está en la base de datos
        titulo = Cuestionario.objects.get().bloques.get().titulo
        self.assertEqual(titulo.fotos.count(), 1)
        foto = titulo.fotos.get()
        self.assertEqual(foto.id, foto_id)

        # probar que la informacion se pueda obtener
        bloque = self.request_cuestionario_y_obtener_bloque(id_cuestionario)

        titulo = bloque['titulo']
        self.assertEqual(titulo['id'], str(id_titulo))
        self.assertEqual(titulo['titulo'], 'tit')
        self.assertEqual(titulo['descripcion'], 'desc')
        self.assertEqual(len(titulo['fotos_urls']), 1)
        foto = titulo['fotos_urls'][0]
        self.assertTrue(foto['foto'].startswith('http://testserver/media/fotos_cuestionarios/'))

    def test_crear_cuestionario_con_pregunta_de_seleccion_unica(self):
        (response, id_cuestionario), id_pregunta, id_opcion = self.crear_cuestionario_con_pregunta_de_seleccion_unica()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # probar que la informacion está en la base de datos
        pregunta = Cuestionario.objects.get().bloques.get().pregunta
        self.assertEqual(pregunta.fotos_guia.count(), 1)
        self.assertEqual(pregunta.etiquetas.count(), 1)
        self.assertEqual(pregunta.opciones_de_respuesta.count(), 1)

        # probar que la informacion se pueda obtener
        bloque = self.request_cuestionario_y_obtener_bloque(id_cuestionario)

        pregunta = bloque['pregunta']
        self.assertEqual(pregunta['id'], str(id_pregunta))
        foto = pregunta['fotos_guia_urls'][0]
        self.assertTrue(foto['foto'].startswith('http://testserver/media/fotos_cuestionarios/'))
        self.assertEqual(pregunta['tipo_de_pregunta'], 'seleccion_unica')
        opcion_de_respuesta = pregunta['opciones_de_respuesta'][0]
        self.assertEqual(opcion_de_respuesta['id'], str(id_opcion))

    def test_crear_cuestionario_con_pregunta_de_seleccion_multiple(self):
        (response,
         id_cuestionario), id_pregunta, id_opcion = self.crear_cuestionario_con_pregunta_de_seleccion_multiple()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # probar que la informacion está en la base de datos
        pregunta = Cuestionario.objects.get().bloques.get().pregunta
        self.assertEqual(pregunta.fotos_guia.count(), 1)
        self.assertEqual(pregunta.etiquetas.count(), 1)
        self.assertEqual(pregunta.opciones_de_respuesta.count(), 1)

        # probar que la informacion se pueda obtener
        bloque = self.request_cuestionario_y_obtener_bloque(id_cuestionario)

        pregunta = bloque['pregunta']
        self.assertEqual(pregunta['id'], str(id_pregunta))
        self.assertEqual(pregunta['tipo_de_pregunta'], 'seleccion_multiple')
        opcion_de_respuesta = pregunta['opciones_de_respuesta'][0]
        self.assertEqual(opcion_de_respuesta, {'id': str(id_opcion), 'titulo': 'tit',
                                               'descripcion': 'desc', 'criticidad': 1,
                                               'requiere_criticidad_del_inspector': False,
                                               })

    def test_crear_cuestionario_con_pregunta_de_tipo_desconocido(self):
        id_pregunta = uuid.uuid4()
        id_opcion = uuid.uuid4()
        response, id_cuestionario = self.crear_cuestionario_con_bloque(
            pregunta={'id': id_pregunta, 'titulo': 'tit', 'descripcion': 'desc',
                      'criticidad': 1,
                      'etiquetas': [{'clave': 'sistema', 'valor': 'motor'}],
                      'nombres_fotos': [{'nombre_subida': 'foto1.jpg'}],
                      'tipo_de_pregunta': 'capybara',
                      'opciones_de_respuesta': [
                          {'id': id_opcion, 'titulo': 'tit',
                           'descripcion': 'desc', 'criticidad': 1
                           }]
                      })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['bloques'][0]['pregunta']['tipo_de_pregunta'][0].code, 'invalid_choice')

        # probar que la informacion no está en la base de datos
        self.assertEqual(Cuestionario.objects.count(), 0)
        self.assertEqual(Bloque.objects.count(), 0)
        self.assertEqual(Pregunta.objects.count(), 0)
        self.assertEqual(OpcionDeRespuesta.objects.count(), 0)

    def test_crear_cuestionario_con_pregunta_numerica(self):
        (response,
         id_cuestionario), id_pregunta, id_criticidad = self.crear_cuestionario_con_pregunta_numerica()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # probar que la informacion está en la base de datos
        pregunta = Cuestionario.objects.get().bloques.get().pregunta
        self.assertEqual(pregunta.fotos_guia.count(), 1)
        self.assertEqual(pregunta.etiquetas.count(), 1)
        self.assertEqual(pregunta.opciones_de_respuesta.count(), 0)
        self.assertEqual(pregunta.criticidades_numericas.count(), 1)

        # probar que la informacion se pueda obtener
        bloque = self.request_cuestionario_y_obtener_bloque(id_cuestionario)

        pregunta = bloque['pregunta']
        self.assertEqual(pregunta['id'], str(id_pregunta))
        self.assertEqual(pregunta['tipo_de_pregunta'], 'numerica')
        criticidad_numerica = pregunta['criticidades_numericas'][0]
        self.assertEqual(criticidad_numerica, {'id': str(id_criticidad), 'criticidad': 1, 'valor_minimo': 0,
                                               'valor_maximo': 10})

    def test_crear_cuestionario_con_cuadricula(self):
        (response, id_cuestionario), id_pregunta, id_opcion, id_subpregunta = \
            self.crear_cuestionario_con_pregunta_de_cuadricula()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # probar que la informacion está en la base de datos
        cuadricula = Cuestionario.objects.get().bloques.get().pregunta
        self.assertEqual(cuadricula.fotos_guia.count(), 1)
        self.assertEqual(cuadricula.etiquetas.count(), 1)
        self.assertEqual(cuadricula.opciones_de_respuesta.count(), 1)
        self.assertEqual(cuadricula.preguntas.count(), 1)
        subpregunta = cuadricula.preguntas.get()
        self.assertEqual(subpregunta.fotos_guia.count(), 0)
        self.assertEqual(subpregunta.etiquetas.count(), 0)
        self.assertEqual(subpregunta.opciones_de_respuesta.count(), 0)
        self.assertEqual(subpregunta.preguntas.count(), 0)

        # probar que la informacion se pueda obtener
        bloque = self.request_cuestionario_y_obtener_bloque(id_cuestionario)

        cuadricula = bloque['pregunta']
        self.assertEqual(cuadricula['id'], str(id_pregunta))
        self.assertEqual(cuadricula['tipo_de_pregunta'], 'cuadricula')
        self.assertEqual(cuadricula['tipo_de_cuadricula'], 'seleccion_unica')
        opcion_de_respuesta = cuadricula['opciones_de_respuesta'][0]
        self.assertEqual(opcion_de_respuesta['id'], str(id_opcion))
        subpregunta = cuadricula['preguntas'][0]
        self.assertEqual(subpregunta['id'], str(id_subpregunta))
