import uuid

import django.db.utils
from django.db import transaction

from inspecciones.models import Cuestionario, Bloque, OpcionDeRespuesta, Pregunta
from inspecciones.tests.test_classes import InspeccionesAuthenticatedTestCase


class ConstraintsTest(InspeccionesAuthenticatedTestCase):
    def test_pregunta_debe_estar_asociada_solo_a_bloque_o_cuadricula(self):
        cuestionario = Cuestionario.objects.create(id=uuid.uuid4(), tipo_de_inspeccion='preoperacional', version=1,
                                                   estado=Cuestionario.EstadoDeCuestionario.finalizado,
                                                   periodicidad_dias=1, organizacion=self.organizacion,
                                                   creador=self.perfil)
        bloque1 = Bloque.objects.create(id=uuid.uuid4(), n_orden=1, cuestionario=cuestionario)
        bloque2 = Bloque.objects.create(id=uuid.uuid4(), n_orden=2, cuestionario=cuestionario)
        opcion_de_respuesta = OpcionDeRespuesta.objects.create(id=uuid.uuid4(), titulo='opcion', descripcion='d',
                                                               criticidad=1, requiere_criticidad_del_inspector=False,)

        cuadricula = Pregunta.objects.create(id=uuid.uuid4(), titulo='tit', descripcion='desc', criticidad=1,
                                             tipo_de_pregunta=Pregunta.TiposDePregunta.cuadricula,
                                             tipo_de_cuadricula=Pregunta.TiposDeCuadricula.seleccion_unica,
                                             bloque=bloque2)

        # con bloque sin error
        Pregunta.objects.create(id=uuid.uuid4(), titulo='tit', descripcion='desc', criticidad=1,
                                tipo_de_pregunta=Pregunta.TiposDePregunta.seleccion_unica,
                                bloque=bloque1)

        # con cuadricula sin error
        Pregunta.objects.create(id=uuid.uuid4(), titulo='tit', descripcion='desc', criticidad=1,
                                tipo_de_pregunta=Pregunta.TiposDePregunta.parte_de_cuadricula,
                                cuadricula=cuadricula)

        # con bloque y cuadricula con error
        with self.assertRaises(django.db.utils.IntegrityError):
            with transaction.atomic():
                Pregunta.objects.create(id=uuid.uuid4(), titulo='tit', descripcion='desc', criticidad=1,
                                        tipo_de_pregunta=Pregunta.TiposDePregunta.parte_de_cuadricula,
                                        bloque=bloque1, cuadricula=cuadricula)

        with self.assertRaises(django.db.utils.IntegrityError):
            with transaction.atomic():
                Pregunta.objects.create(id=uuid.uuid4(), titulo='tit', descripcion='desc', criticidad=1,
                                        tipo_de_pregunta=Pregunta.TiposDePregunta.parte_de_cuadricula)
