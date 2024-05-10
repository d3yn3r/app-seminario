from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from rest_framework.response import Response
from rest_framework.settings import api_settings

from inspecciones.mixins import PutAsCreateMixin, CreateAsUpdateMixin
from inspecciones.models import Perfil, Organizacion, Activo, Cuestionario, Inspeccion, EtiquetaJerarquicaDeActivo, \
    EtiquetaJerarquicaDePregunta
from inspecciones.serializers import PerfilCreateSerializer, \
    OrganizacionSerializer, ActivoSerializer, CuestionarioSerializer, CuestionarioCompletoSerializer, \
    InspeccionCompletaSerializer, PerfilSerializer, \
    SubirFotosCuestionarioSerializer, SubirFotosInspeccionSerializer, EtiquetaJerarquicaDeActivoSerializer, \
    EtiquetaJerarquicaDePreguntaSerializer
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.shortcuts import redirect

@never_cache
def custom_logout(request):
    """
    Vista personalizada para cerrar sesión.
    """
    logout(request)
    # Redirige a la página de inicio de sesión o a cualquier otra página que desees después de cerrar sesión.
    return redirect('login')

class OrganizacionViewSet(viewsets.ModelViewSet):
    queryset = Organizacion.objects.all()
    serializer_class = OrganizacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def mi_organizacion(self, request):
        self.kwargs['pk'] = request.user.perfil.organizacion.pk
        return self.retrieve(request)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in {'retrieve', 'list', 'destroy'}:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
        return [permission() for permission in permission_classes]

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers that this view can use.
        """
        if self.action == 'create':
            parser_classes = [MultiPartParser]
        else:
            parser_classes = api_settings.DEFAULT_PARSER_CLASSES

        return [parser() for parser in parser_classes]

    def initialize_request(self, request, *args, **kwargs):
        """Machete para que [get_permissions] pueda conocer [self.action] """
        self.action = self.action_map.get(request.method.lower())
        return super().initialize_request(request, *args, **kwargs)

    def get_queryset(self):
        # solo conoce los perfiles que pertenecen a la organizacion del perfil actual
        return Perfil.objects.filter(organizacion=self.request.user.perfil.organizacion)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        if self.action == 'list':
            kwargs.setdefault('fields', ['id', 'nombre', 'foto', 'rol'])
        elif self.action in {'retrieve', 'mi_perfil'}:
            kwargs.setdefault('fields', ['id', 'esta_activo', 'fecha_registro', 'username', 'nombre', 'email', 'foto',
                                         'celular', 'organizacion', 'rol'])
        return serializer_class(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = PerfilCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        res = serializer.save()
        return Response(res, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        perfil = self.get_object()
        user = perfil.user
        self.perform_destroy(user)
        self.perform_destroy(perfil)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        self.kwargs['pk'] = request.user.perfil.pk
        return self.retrieve(request)


class EtiquetaJerarquicaDeActivoViewSet(CreateAsUpdateMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        return EtiquetaJerarquicaDeActivo.objects.filter(organizacion=self.request.user.perfil.organizacion)

    serializer_class = EtiquetaJerarquicaDeActivoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'nombre'


class EtiquetaJerarquicaDePreguntaViewSet(CreateAsUpdateMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        return EtiquetaJerarquicaDePregunta.objects.filter(organizacion=self.request.user.perfil.organizacion)

    serializer_class = EtiquetaJerarquicaDePreguntaSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'nombre'


class ActivoViewSet(viewsets.ModelViewSet):


    def get_queryset(self):
        # solo muestra los activos que pertenecen a la organizacion del perfil actual
        return Activo.objects.filter(organizacion=self.request.user.perfil.organizacion)

    serializer_class = ActivoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """metodo de creacion modificado para que acepte listas tambien, usado en la carga masiva con excel"""
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        if many:
            super(viewsets.ModelViewSet, self).perform_create(serializer)
        else:
            self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)


class CuestionarioViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # solo muestra los cuestionarios que pertenecen a la organizacion del perfil actual
        return Cuestionario.objects.filter(organizacion=self.request.user.perfil.organizacion)

    serializer_class = CuestionarioSerializer
    permission_classes = [permissions.IsAuthenticated]


class CuestionarioCompletoViewSet(CuestionarioViewSet):
    serializer_class = CuestionarioCompletoSerializer

    @action(detail=False, methods=['post'])
    def subir_fotos(self, request):
        serializer = SubirFotosCuestionarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        res = serializer.save()
        return Response(res, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Hace un update a la berraca, borrando todo y volviendolo a insertar
        TODO: hacer tests para este metodo"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.create(request, *args, **kwargs)


class InspeccionCompletaViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        user = self.request.user
        # solo muestra las inspecciones de la organizacion del perfil actual
        return Inspeccion.objects.filter(cuestionario__organizacion=user.perfil.organizacion)

    serializer_class = InspeccionCompletaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def subir_fotos(self, request):
        serializer = SubirFotosInspeccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        res = serializer.save()
        return Response(res, status=status.HTTP_201_CREATED)
