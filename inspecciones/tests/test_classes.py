import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from inspecciones.models import Organizacion, Perfil, Activo, FotoCuestionario, FotoRespuesta


class InspeccionesAuthenticatedTestCase(APITestCase):
    """Esta clase antes de ejecutar cada test crea una organizacion [self.organizacion] y un usuario administrador
    [self.perfil] perteneciente a esta y realiza la autenticacion en el [self.client], tambien crea un activo [self.activo]"""

    def setUp(self):
        self._crear_admin_y_autenticar()
        self.activo = Activo.objects.create(identificador="a1", organizacion=self.organizacion)
        _, foto_cuestionario_id = self.subir_foto_cuestionario()
        self.foto_cuestionario = FotoCuestionario.objects.get(id=foto_cuestionario_id)
        _, foto_inspeccion_id1 = self.subir_foto_inspeccion()
        _, foto_inspeccion_id2 = self.subir_foto_inspeccion()
        self.foto_inspeccion1 = FotoRespuesta.objects.get(id=foto_inspeccion_id1)
        self.foto_inspeccion2 = FotoRespuesta.objects.get(id=foto_inspeccion_id2)
        super().setUp()

    def tearDown(self) -> None:
        self.foto_cuestionario.foto.delete()
        self.foto_inspeccion1.foto.delete()
        self.foto_inspeccion2.foto.delete()
        super().tearDown()

    def _crear_admin_y_autenticar(self):
        self.user = get_user_model().objects.create_user(username='gato', first_name="gato", password='gato')
        self.organizacion = Organizacion.objects.create(nombre="gomac")
        self.perfil = Perfil.objects.create(user=self.user, celular="123", organizacion=self.organizacion,
                                            rol=Perfil.Roles.administrador)
        self.client.force_authenticate(user=self.user)

    def crear_cuestionario(self, bloques=None):
        url = reverse('api:cuestionario-completo-list')
        id_cuestionario = uuid.uuid4()

        return self.client.post(url, {'id': id_cuestionario, 'tipo_de_inspeccion': 'preoperacional',
                                      'version': 1, 'estado': 'finalizado',
                                      'periodicidad_dias': 1, 'etiquetas_aplicables': [], 'bloques': bloques,
                                      },
                                format='json'), id_cuestionario

    def crear_cuestionario_con_bloque(self, **kwargs):
        return self.crear_cuestionario(bloques=[{'n_orden': 1, **kwargs}])

    def crear_cuestionario_con_pregunta_de_seleccion_unica(self):
        id_pregunta = uuid.uuid4()
        id_opcion = uuid.uuid4()
        return self.crear_cuestionario_con_bloque(
            pregunta={'id': id_pregunta, 'titulo': 'tit', 'descripcion': 'desc',
                      'criticidad': 1,
                      'etiquetas': [{'clave': 'sistema', 'valor': 'motor'}],
                      'fotos_guia': [self.foto_cuestionario.id],
                      'tipo_de_pregunta': 'seleccion_unica',
                      'opciones_de_respuesta': [
                          {'id': id_opcion, 'titulo': 'tit',
                           'descripcion': 'desc', 'criticidad': 1, 'requiere_criticidad_del_inspector': False,
                           }]
                      }), id_pregunta, id_opcion

    def crear_cuestionario_con_pregunta_de_seleccion_multiple(self):
        id_pregunta = uuid.uuid4()
        id_opcion = uuid.uuid4()
        return self.crear_cuestionario_con_bloque(
            pregunta={'id': id_pregunta, 'titulo': 'tit', 'descripcion': 'desc',
                      'criticidad': 1,
                      'etiquetas': [{'clave': 'sistema', 'valor': 'motor'}],
                      'fotos_guia': [self.foto_cuestionario.id],
                      'tipo_de_pregunta': 'seleccion_multiple',
                      'opciones_de_respuesta': [
                          {'id': id_opcion, 'titulo': 'tit',
                           'descripcion': 'desc', 'criticidad': 1, 'requiere_criticidad_del_inspector': False,
                           }]
                      }), id_pregunta, id_opcion

    def crear_cuestionario_con_pregunta_numerica(self):
        id_pregunta = uuid.uuid4()
        id_criticidad = uuid.uuid4()
        return self.crear_cuestionario_con_bloque(
            pregunta={'id': id_pregunta, 'titulo': 'tit', 'descripcion': 'desc',
                      'criticidad': 1,
                      'etiquetas': [{'clave': 'sistema', 'valor': 'motor'}],
                      'fotos_guia': [self.foto_cuestionario.id],
                      'tipo_de_pregunta': 'numerica',
                      'criticidades_numericas': [
                          {'id': id_criticidad, 'criticidad': 1, 'valor_minimo': 0, 'valor_maximo': 10}]
                      }), id_pregunta, id_criticidad

    def crear_cuestionario_con_pregunta_de_cuadricula(self):
        id_pregunta = uuid.uuid4()
        id_opcion = uuid.uuid4()
        id_subpregunta = uuid.uuid4()
        return self.crear_cuestionario_con_bloque(
            pregunta={'id': id_pregunta, 'titulo': 'cuadricula', 'descripcion': 'desc',
                      'criticidad': 1,
                      'etiquetas': [{'clave': 'sistema', 'valor': 'motor'}],
                      'fotos_guia': [self.foto_cuestionario.id],
                      'tipo_de_pregunta': 'cuadricula',
                      'tipo_de_cuadricula': 'seleccion_unica',
                      'opciones_de_respuesta': [
                          {'id': id_opcion, 'titulo': 'tit',
                           'descripcion': 'desc', 'criticidad': 1, 'requiere_criticidad_del_inspector': False,
                           }],
                      'preguntas': [
                          {'id': id_subpregunta, 'titulo': 'tit', 'descripcion': '', 'criticidad': 1,
                           'tipo_de_pregunta': 'parte_de_cuadricula'}
                      ]
                      }), id_pregunta, id_opcion, id_subpregunta

    def crear_inspeccion(self, id_cuestionario, respuestas=None):
        url = reverse('api:inspeccion-completa-list')
        id_inspeccion = uuid.uuid4()

        return self.client.post(url, {'id': id_inspeccion, 'cuestionario': id_cuestionario,
                                      'momento_inicio': '2020-01-01T00:00:00Z', 'activo': self.activo.id,
                                      'criticidad_calculada': 0, 'criticidad_calculada_con_reparaciones': 0,
                                      'estado': 'borrador',
                                      'respuestas': respuestas},
                                format='json'), id_inspeccion

    def _build_respuesta(self, id_pregunta, **kwargs):
        return {'pregunta': id_pregunta,
                'fotos_base': [self.foto_inspeccion1.id],
                'fotos_reparacion': [self.foto_inspeccion2.id],
                'reparado': False,
                'observacion': 'observacion',
                'observacion_reparacion': 'observacion reparacion',
                'momento_respuesta': '2020-01-01T00:00:00Z',
                'criticidad_del_inspector': None,
                'criticidad_calculada': 0,
                'criticidad_calculada_con_reparaciones': 0,
                **kwargs}

    def crear_inspeccion_con_respuesta_de_seleccion_unica(self, id_cuestionario, id_pregunta, id_opcion):
        return self.crear_inspeccion(id_cuestionario, respuestas=[
            self._build_respuesta(id_pregunta,
                                  tipo_de_respuesta='seleccion_unica',
                                  opcion_seleccionada=id_opcion)
        ])

    def crear_inspeccion_con_respuesta_numerica(self, id_cuestionario, id_pregunta):
        return self.crear_inspeccion(id_cuestionario, respuestas=[
            self._build_respuesta(id_pregunta,
                                  tipo_de_respuesta='numerica',
                                  valor_numerico=5)
        ])

    def crear_inspeccion_con_respuesta_de_seleccion_multiple(self, id_cuestionario, id_pregunta, id_opcion):
        return self.crear_inspeccion(id_cuestionario, respuestas=[
            self._build_respuesta(id_pregunta,
                                  tipo_de_respuesta='seleccion_multiple',
                                  subrespuestas_multiple=[
                                      self._build_respuesta(None,
                                                            tipo_de_respuesta='parte_de_seleccion_multiple',
                                                            opcion_respondida=id_opcion,
                                                            opcion_respondida_esta_seleccionada=True)
                                  ])
        ])

    def crear_inspeccion_con_respuesta_de_cuadricula(self, id_cuestionario, id_pregunta, id_opcion,
                                                     id_subpregunta):

        return self.crear_inspeccion(id_cuestionario, respuestas=[
            self._build_respuesta(id_pregunta,
                                  tipo_de_respuesta='cuadricula',
                                  subrespuestas_cuadricula=[
                                      self._build_respuesta(id_subpregunta,
                                                            tipo_de_respuesta='seleccion_unica',
                                                            opcion_seleccionada=id_opcion)
                                  ])
        ])

    def subir_foto_cuestionario(self):
        url = reverse('api:cuestionario-completo-subir-fotos')
        with open('media/perfil.png', 'rb') as foto:
            response = self.client.post(url, {'fotos': [foto]})
        return response, response.data['perfil.png']

    def subir_foto_inspeccion(self):
        url = reverse('api:inspeccion-completa-subir-fotos')
        with open('media/perfil.png', 'rb') as foto:
            response = self.client.post(url, {'fotos': [foto]})
        return response, response.data['perfil.png']
