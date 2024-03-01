from django.urls import reverse
from rest_framework import status

from inspecciones.models import FotoCuestionario
from inspecciones.tests.test_classes import InspeccionesAuthenticatedTestCase


class SubirFotosTest(InspeccionesAuthenticatedTestCase):
    def test_subir_fotos_cuestionario(self):
        response, foto_id = self.subir_foto_cuestionario()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(str(foto_id)), 36)

        self.assertEqual(FotoCuestionario.objects.count(), 2)  # 1 foto subida por la clase padre y otra por este test
        foto = FotoCuestionario.objects.get(id=foto_id)
        self.assertEqual(foto.object_id, None)
        foto.foto.delete()
