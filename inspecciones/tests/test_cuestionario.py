import uuid
from collections import OrderedDict

from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
import django.db.utils

from .test_classes import InspeccionesAuthenticatedTestCase
from .. import serializers
from ..models import Cuestionario, OpcionDeRespuesta, Pregunta, Bloque


class CuestionarioTest(InspeccionesAuthenticatedTestCase):
    def test_crear_cuestionario(self):
        id_local = uuid.uuid4()
        url = reverse('api:cuestionario-list')
        response = self.client.post(url, {'id': id_local, 'tipo_de_inspeccion': 'preventivo', 'version': 1,
                                          'estado': 'finalizado', 'periodicidad_dias': 1, 'etiquetas_aplicables': []},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cuestionario.objects.count(), 1)
        cuestionario = Cuestionario.objects.get()
        self.assertEqual(cuestionario.organizacion, self.organizacion)
        self.assertEqual(cuestionario.creador, self.perfil)
        self.assertEqual(cuestionario.id, id_local)

    def test_no_se_permite_crear_cuestionario_sin_id(self):
        url_crear = reverse('api:cuestionario-list')

        response_creacion = self.client.post(url_crear, {'tipo_de_inspeccion': 'preoperacional', 'version': 1,
                                                         'periodicidad_dias': 1, 'etiquetas_aplicables': []},
                                             format='json')
        self.assertEqual(response_creacion.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cuestionario.objects.count(), 0)


    def test_ver_cuestionario(self):
        id_local = uuid.uuid4()
        cuestionario = Cuestionario.objects.create(id=id_local, tipo_de_inspeccion='preoperacional', version=1,
                                                   estado=Cuestionario.EstadoDeCuestionario.finalizado,
                                                   periodicidad_dias=1, organizacion=self.organizacion,
                                                   creador=self.perfil)

        url_detalle = reverse('api:cuestionario-detail', kwargs={'pk': id_local})
        response = self.client.get(url_detalle, {'id': url_detalle})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        momento_subida = response.data.pop('momento_subida')
        self.assertEqual(response.data, {'id': str(id_local), 'etiquetas_aplicables': [], 'creador': 1,
                                         'estado': 'finalizado',
                                         'tipo_de_inspeccion': 'preoperacional', 'version': 1, 'periodicidad_dias': 1})

    def test_lista_cuestionarios(self):
        id_local = uuid.uuid4()
        cuestionario = Cuestionario.objects.create(id=id_local, tipo_de_inspeccion='preoperacional', version=1,
                                                   estado=Cuestionario.EstadoDeCuestionario.finalizado,
                                                   periodicidad_dias=1, organizacion=self.organizacion,
                                                   creador=self.perfil)

        url = reverse('api:cuestionario-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        momento_subida = response.data[0].pop('momento_subida')
        self.assertEqual(response.data[0], {'id': str(id_local), 'etiquetas_aplicables': [], 'creador': 1,
                                            'estado': 'finalizado',
                                            'tipo_de_inspeccion': 'preoperacional', 'version': 1,
                                            'periodicidad_dias': 1})
