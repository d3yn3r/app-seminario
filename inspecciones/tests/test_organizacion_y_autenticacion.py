import django.test
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

import inspecciones.serializers as serializers
from ..models import Organizacion, Perfil, Activo, EtiquetaDeActivo
from .test_classes import InspeccionesAuthenticatedTestCase


class RegistroUsuarioTest(APITestCase):
    def setUp(self):
        Organizacion.objects.create(nombre='laga_inc')
        self.url = reverse('api:user-list')

        self.registro_form = {'username': 'gato', 'nombre': 'juan daniel', 'apellido': 'perez',
                              'email': 'jp@gmail.com', 'password': '123', 'celular': '123',
                              'organizacion': 1}

    def test_registro_usuario_con_foto(self):
        with open('media/perfil.png', 'rb') as foto:
            self.registro_form['foto'] = foto
            response = self.client.post(self.url, self.registro_form)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Perfil.objects.count(), 1)
        self.assertEqual(Perfil.objects.get().foto.url, '/media/fotos_perfiles/perfil.png')

        Perfil.objects.get().foto.delete()

    def test_registro_usuario_sin_foto(self):
        response = self.client.post(self.url, self.registro_form)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Perfil.objects.count(), 1)

    def test_registro_usuario_generar_username(self):
        self.registro_form.pop('username')
        response = self.client.post(self.url, self.registro_form)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.get().username, 'juan')

    def test_registro_usuario_generar_consecutivo(self):
        get_user_model().objects.create_user(username='juan')
        self.registro_form.pop('username')
        response = self.client.post(self.url, self.registro_form)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        get_user_model().objects.get(username='juan1')  # si lanza excepcion es porque no existe


class ListaUsuariosTest(InspeccionesAuthenticatedTestCase):
    def test_lista_usuarios(self):
        otra_org = Organizacion.objects.create(nombre="otraorg")
        user1 = get_user_model().objects.create_user(username='testuser1', first_name="testuser1", password='12345')
        Perfil.objects.create(user=user1, celular="123", organizacion=self.organizacion, rol=Perfil.Roles.inspector)
        user2 = get_user_model().objects.create_user(username='testuser2', first_name="testuser2", password='12345')
        Perfil.objects.create(user=user2, celular="123", organizacion=otra_org, rol=Perfil.Roles.inspector)

        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data,
                         [{'id': 1, 'nombre': 'gato', 'foto': 'http://testserver/media/blank.jpg',
                           'rol': 'administrador'},
                          {'id': 2, 'nombre': 'testuser1', 'foto': 'http://testserver/media/blank.jpg',
                           'rol': 'inspector'}])


class RetrieveUsuarioTest(InspeccionesAuthenticatedTestCase):
    def test_ver_usuario(self):
        user1 = get_user_model().objects.create_user(username='testuser1', email='tu@gmail.com', first_name="testuser1",
                                                     password='12345')
        perfil1 = Perfil.objects.create(user=user1, celular="123", organizacion=self.organizacion,
                                        rol=Perfil.Roles.inspector)

        response = self.client.get(reverse('api:user-detail', args=[perfil1.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.data.pop('fecha_registro')
        self.assertEqual(response.data,
                         {'id': 2, 'esta_activo': True, 'username': 'testuser1', 'nombre': 'testuser1',
                          'email': 'tu@gmail.com', 'foto': 'http://testserver/media/blank.jpg', 'celular': '123',
                          'organizacion': 'gomac', 'rol': 'inspector'})

    def test_mi_perfil(self):
        response = self.client.get(reverse('api:user-mi-perfil'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.data.pop('fecha_registro')
        self.assertEqual(response.data,
                         {'id': 1, 'esta_activo': True, 'username': 'gato', 'nombre': 'gato', 'email': '',
                          'foto': 'http://testserver/media/blank.jpg', 'celular': '123', 'organizacion': 'gomac',
                          'rol': 'administrador'})

    def test_la_url_de_la_foto_debe_ser_absoluta_y_generada(self):
        response = self.client.get(reverse('api:user-mi-perfil'), SERVER_NAME="anotherdomain.com")
        self.assertEqual(response.data['foto'], 'http://anotherdomain.com/media/blank.jpg')


class DestroyUsuarioTest(InspeccionesAuthenticatedTestCase):
    def test_ver_usuario(self):
        user1 = get_user_model().objects.create_user(username='testuser1', email='tu@gmail.com', first_name="testuser1",
                                                     password='12345')
        perfil1 = Perfil.objects.create(user=user1, celular="123", organizacion=self.organizacion,
                                        rol=Perfil.Roles.inspector)

        response = self.client.delete(reverse('api:user-detail', args=[perfil1.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Perfil.objects.filter(user=user1).count(), 0)
        self.assertEqual(get_user_model().objects.filter(username='testuser1').count(), 0)


class CrearOrganizacionTest(InspeccionesAuthenticatedTestCase):
    def test_crear_organizacion(self):
        url = reverse('api:organizacion-list')
        with open('media/perfil.png', 'rb') as foto:
            response = self.client.post(url, {'nombre': 'gomac2', 'logo': foto, 'link': 'https://gomac.com',
                                              'acerca': 'gomac'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organizacion.objects.count(), 2)  # la del admin autenticado y la nueva
        org = Organizacion.objects.get(nombre='gomac2')
        self.assertEqual(org.link, 'https://gomac.com')
        Organizacion.objects.get(nombre='gomac2').logo.delete()


class ActivoTest(InspeccionesAuthenticatedTestCase):
    def test_crear_activo(self):
        activo_id = 'fas564'
        url = reverse('api:activo-detail', kwargs={'pk': activo_id})

        response = self.client.put(url, {'identificador': activo_id, 'etiquetas': [{'clave': 'modelo', 'valor': 'carro'}]},
                                   format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Activo.objects.count(), 2)  # el que crea la clase padre para pruebas, y el nuevo
        activo = Activo.objects.get(identificador=activo_id)
        self.assertEqual(activo.organizacion.nombre, 'gomac')
        self.assertEqual(activo.etiquetas.first().clave, 'modelo')
        self.assertEqual(activo.etiquetas.first().valor, 'carro')

    def test_actualizar_activo(self):
        activo_id = 'fas564'
        url = reverse('api:activo-detail', kwargs={'pk': activo_id})

        response1 = self.client.put(url, {'identificador': activo_id, 'etiquetas': [{'clave': 'modelo', 'valor': 'carro'},
                                                                         {'clave': 'marca', 'valor': 'ford'}]},
                                    format='json')

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Activo.objects.count(), 2)  # el que crea la clase padre para otras pruebas, y el nuevo
        activo = Activo.objects.get(identificador=activo_id)
        self.assertEqual(activo.organizacion.nombre, 'gomac')
        self.assertEqual(activo.etiquetas.count(), 2)
        self.assertEqual(activo.etiquetas.first().clave, 'modelo')
        self.assertEqual(activo.etiquetas.first().valor, 'carro')

        response2 = self.client.put(url, {'identificador': activo_id, 'etiquetas': [{'clave': 'marca', 'valor': 'kenworth'}]},
                                    format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Activo.objects.count(), 2)
        activo = Activo.objects.get(identificador=activo_id)
        self.assertEqual(activo.organizacion.nombre, 'gomac')
        self.assertEqual(activo.etiquetas.count(), 1)
        self.assertEqual(activo.etiquetas.first().clave, 'marca')
        self.assertEqual(activo.etiquetas.first().valor, 'kenworth')

    def test_crear_activo_con_etiqueta_existente(self):
        activo_id = 'fas564'
        url = reverse('api:activo-detail', kwargs={'pk': activo_id})

        EtiquetaDeActivo.objects.create(clave='modelo', valor='carro')

        response = self.client.put(url, {'identificador': activo_id, 'etiquetas': [{'clave': 'modelo', 'valor': 'carro'}]},
                                   format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Activo.objects.count(), 2)  # el que crea la clase padre para pruebas, y el nuevo
        activo = Activo.objects.get(identificador=activo_id)
        self.assertEqual(activo.etiquetas.first().clave, 'modelo')
        self.assertEqual(activo.etiquetas.first().valor, 'carro')
        self.assertEqual(EtiquetaDeActivo.objects.count(), 1)

    def test_crear_activo_sin_etiqueta(self):
        activo_id = 'fas564'
        url = reverse('api:activo-detail', kwargs={'pk': activo_id})

        response = self.client.put(url, {'identificador': activo_id, 'etiquetas': []},
                                   format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_lista_activos(self):
        etiqueta1 = EtiquetaDeActivo.objects.create(clave='modelo', valor='carro')
        etiqueta2 = EtiquetaDeActivo.objects.create(clave='year', valor='2022')
        otra_org = Organizacion.objects.create(nombre="otraorg")
        Activo.objects.create(identificador="fas564", organizacion=self.perfil.organizacion).etiquetas.set([etiqueta1, etiqueta2])
        Activo.objects.create(identificador="fas563", organizacion=otra_org).etiquetas.set([etiqueta1])

        response = self.client.get(reverse('api:activo-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # el que crea la clase padre para pruebas, y el nuevo


class TestActivoSerializer(django.test.TestCase):
    def test_serializer(self):
        serializer = serializers.ActivoSerializer()
        print(repr(serializer))


class TestGetToken(APITestCase):
    def test_get_token(self):
        url = reverse('api-token-auth')
        get_user_model().objects.create_user(username='gato', password='gato')
        response = self.client.post(url, {'username': 'gato', 'password': 'gato'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['token']), 1)
