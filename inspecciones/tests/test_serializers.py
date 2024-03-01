from django.test import TestCase

from inspecciones.serializers import TituloSerializer, RespuestaSerializer


class TestSerializers(TestCase):
    def test_serializer(self):
        serializer = RespuestaSerializer()
        print(repr(serializer))
