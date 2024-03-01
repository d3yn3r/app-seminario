from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from inspecciones.mixins import DynamicFieldsModelSerializer
from inspecciones.models import Perfil, Organizacion, Activo, EtiquetaDeActivo, Cuestionario, Bloque, Titulo, \
    Pregunta, EtiquetaDePregunta, OpcionDeRespuesta, CriticidadNumerica, Inspeccion, Respuesta, FotoRespuesta, \
    FotoCuestionario, EtiquetaJerarquicaDeActivo, EtiquetaJerarquicaDePregunta


class OrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacion
        fields = '__all__'


class PerfilSerializer(DynamicFieldsModelSerializer):
    organizacion = serializers.SerializerMethodField()

    esta_activo = serializers.SerializerMethodField()
    fecha_registro = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    nombre = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Perfil
        fields = '__all__'

    def get_organizacion(self, obj):
        return obj.organizacion.nombre

    def get_esta_activo(self, obj):
        return obj.user.is_active

    def get_fecha_registro(self, obj):
        return obj.user.date_joined

    def get_username(self, obj):
        return obj.user.username

    def get_nombre(self, obj):
        return obj.user.get_full_name()

    def get_email(self, obj):
        return obj.user.email


class PerfilCreateSerializer(serializers.Serializer):
    username = serializers.CharField(allow_blank=True, default='')
    nombre = serializers.CharField()
    apellido = serializers.CharField(allow_blank=True)  # allow_blank: permite string vacio
    email = serializers.EmailField()
    password = serializers.CharField()
    celular = serializers.CharField(max_length=13, allow_blank=True)
    organizacion = serializers.PrimaryKeyRelatedField(queryset=Organizacion.objects.all())
    foto = serializers.ImageField(default='blank.jpg')

    def save(self):
        username = self.validated_data['username']  # si es vacio se genera uno
        nombre = self.validated_data['nombre']
        apellido = self.validated_data['apellido']
        email = self.validated_data['email']
        password = self.validated_data['password']
        celular = self.validated_data['celular']
        organizacion = self.validated_data['organizacion']
        foto = self.validated_data['foto']

        if get_user_model().objects.filter(username=username) or not username.strip():
            username = self._generar_username(username, nombre, apellido)

        user = get_user_model().objects.create_user(username=username, email=email, password=password,
                                                    first_name=nombre, last_name=apellido)

        Perfil.objects.create(user=user, organizacion=organizacion, celular=celular, foto=foto,
                              rol=Perfil.Roles.inspector)

        return {'username': username}

    @staticmethod
    def _generar_username(username: str, nombre: str, apellido: str) -> str:
        if username.strip():
            return PerfilCreateSerializer._agregar_consecutivo(username)
        username = nombre.split(" ")[0]
        return PerfilCreateSerializer._agregar_consecutivo(username)

    @staticmethod
    def _agregar_consecutivo(username: str):
        counter = 1
        posible_username = username
        while get_user_model().objects.filter(username=posible_username):
            posible_username = username + str(counter)
            counter += 1
        return posible_username


class EtiquetaJerarquicaDeActivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtiquetaJerarquicaDeActivo
        fields = ['nombre', 'json']

    def create(self, validated_data):
        return EtiquetaJerarquicaDeActivo.objects.create(organizacion=self.context['request'].user.perfil.organizacion,
                                                         **validated_data)


class EtiquetaJerarquicaDePreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtiquetaJerarquicaDePregunta
        fields = ['nombre', 'json']

    def create(self, validated_data):
        return EtiquetaJerarquicaDePregunta.objects.create(
            organizacion=self.context['request'].user.perfil.organizacion,
            **validated_data)


class EtiquetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtiquetaDeActivo
        fields = ['clave', 'valor']


class ActivoSerializer(serializers.ModelSerializer):
    etiquetas = EtiquetaSerializer(many=True)
    organizacion = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Activo
        fields = '__all__'
        validators = []

    def create(self, validated_data):
        etiquetas_data = validated_data.pop('etiquetas')
        activo = Activo.objects.create(organizacion=self.context['request'].user.perfil.organizacion,
                                       **validated_data)
        for etiqueta in etiquetas_data:
            etiqueta_db, _ = EtiquetaDeActivo.objects.get_or_create(**etiqueta)
            activo.etiquetas.add(etiqueta_db)
        return activo

    def update(self, instance: Activo, validated_data):
        etiquetas_data = validated_data.pop('etiquetas')
        activo = instance
        activo.identificador = validated_data.pop('identificador')
        activo.etiquetas.clear()
        for etiqueta in etiquetas_data:
            etiqueta_db, _ = EtiquetaDeActivo.objects.get_or_create(**etiqueta)
            activo.etiquetas.add(etiqueta_db)
        activo.save()
        return activo


class CuestionarioSerializer(serializers.ModelSerializer):
    etiquetas_aplicables = EtiquetaSerializer(many=True)
    organizacion = None
    creador = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Cuestionario
        exclude = ['organizacion']

    def create(self, validated_data):
        etiquetas_data = validated_data.pop('etiquetas_aplicables')
        perfil = self.context['request'].user.perfil
        cuestionario = Cuestionario.objects.create(creador=perfil, organizacion=perfil.organizacion, **validated_data)
        for etiqueta in etiquetas_data:
            etiqueta_db, _ = EtiquetaDeActivo.objects.get_or_create(**etiqueta)
            cuestionario.etiquetas_aplicables.add(etiqueta_db)
        return cuestionario


class FotoCuestionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoCuestionario
        fields = ['id', 'foto']


class TituloSerializer(serializers.ModelSerializer):
    fotos_urls = FotoCuestionarioSerializer(source='fotos', many=True, read_only=True)
    fotos = serializers.PrimaryKeyRelatedField(many=True, required=False, default=[], write_only=True,
                                               queryset=FotoCuestionario.objects.all())

    class Meta:
        model = Titulo
        exclude = ['bloque']


class OpcionDeRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcionDeRespuesta
        exclude = ['pregunta']


class CriticidadNumericaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticidadNumerica
        exclude = ['pregunta']


class PreguntaSerializer(serializers.ModelSerializer):
    fotos_guia_urls = FotoCuestionarioSerializer(source='fotos_guia', many=True, read_only=True)
    fotos_guia = serializers.PrimaryKeyRelatedField(many=True, required=False, default=[], write_only=True,
                                                    queryset=FotoCuestionario.objects.all())
    etiquetas = EtiquetaSerializer(many=True, required=False, default=[])
    opciones_de_respuesta = OpcionDeRespuestaSerializer(many=True, required=False, default=[])
    criticidades_numericas = CriticidadNumericaSerializer(many=True, required=False, default=[])
    preguntas = RecursiveField(many=True, required=False, default=[])

    class Meta:
        model = Pregunta
        exclude = ['bloque', 'cuadricula']


class BloqueSerializer(serializers.ModelSerializer):
    titulo = TituloSerializer(default=None, allow_null=True, required=False)
    pregunta = PreguntaSerializer(default=None, allow_null=True, required=False)

    class Meta:
        model = Bloque
        exclude = ['cuestionario', 'id']


class CuestionarioCompletoSerializer(CuestionarioSerializer):
    bloques = BloqueSerializer(many=True)

    def create(self, validated_data):
        bloques_data = validated_data.pop('bloques')
        cuestionario = super().create(validated_data)
        for bloque_data in bloques_data:
            self._crear_bloque(cuestionario, bloque_data)
        return cuestionario

    def _crear_bloque(self, cuestionario, bloque_data):
        titulo_data = bloque_data.pop('titulo')
        pregunta_data = bloque_data.pop('pregunta')

        bloque = Bloque.objects.create(cuestionario=cuestionario, **bloque_data)
        if titulo_data is not None:
            self._crear_titulo(bloque, titulo_data)
        if pregunta_data is not None:
            self._crear_pregunta(pregunta_data, bloque=bloque)
        # TODO: validar que venga o un titulo o una pregunta o una cuadricula

    def _crear_titulo(self, bloque, titulo_data):
        fotos_data = titulo_data.pop('fotos')
        titulo = Titulo.objects.create(bloque=bloque, **titulo_data)
        for foto_data in fotos_data:
            titulo.fotos.add(foto_data)

    def _crear_pregunta(self, pregunta_data, bloque=None, cuadricula=None):
        fotos_data = pregunta_data.pop('fotos_guia')
        etiquetas_data = pregunta_data.pop('etiquetas')
        opciones_de_respuesta_data = pregunta_data.pop('opciones_de_respuesta')
        criticidades_numericas_data = pregunta_data.pop('criticidades_numericas')
        preguntas_data = pregunta_data.pop('preguntas')
        pregunta = Pregunta.objects.create(bloque=bloque, cuadricula=cuadricula, **pregunta_data)
        for foto_data in fotos_data:
            pregunta.fotos_guia.add(foto_data)
        for etiqueta_data in etiquetas_data:
            self._crear_etiqueta(pregunta, etiqueta_data)
        for opcion_de_respuesta_data in opciones_de_respuesta_data:
            self._crear_opcion_de_respuesta(pregunta, opcion_de_respuesta_data)
        for criticidad_numerica_data in criticidades_numericas_data:
            self._crear_criticidad_numerica(pregunta, criticidad_numerica_data)
        for pregunta_data in preguntas_data:
            self._crear_pregunta(pregunta_data, cuadricula=pregunta)

    def _crear_etiqueta(self, pregunta, etiqueta_data):
        etiqueta_db, _ = EtiquetaDePregunta.objects.get_or_create(**etiqueta_data)
        pregunta.etiquetas.add(etiqueta_db)

    def _crear_opcion_de_respuesta(self, pregunta, opcion_de_respuesta_data):
        OpcionDeRespuesta.objects.create(pregunta=pregunta, **opcion_de_respuesta_data)

    def _crear_criticidad_numerica(self, pregunta, criticidad_numerica_data):
        CriticidadNumerica.objects.create(pregunta=pregunta, **criticidad_numerica_data)


class FotoRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoRespuesta
        fields = '__all__'


class RespuestaSerializer(serializers.ModelSerializer):
    fotos_base_url = FotoRespuestaSerializer(source='fotos_base', many=True, read_only=True)
    fotos_base = serializers.PrimaryKeyRelatedField(many=True, required=False, default=[], write_only=True,
                                                    queryset=FotoRespuesta.objects.all())
    fotos_reparacion_url = FotoRespuestaSerializer(source='fotos_reparacion', many=True, read_only=True)
    fotos_reparacion = serializers.PrimaryKeyRelatedField(many=True, required=False, default=[], write_only=True,
                                                          queryset=FotoRespuesta.objects.all())

    subrespuestas_cuadricula = RecursiveField(many=True, required=False, default=[])
    subrespuestas_multiple = RecursiveField(many=True, required=False, default=[])

    class Meta:
        model = Respuesta
        exclude = ['inspeccion']


class InspeccionCompletaSerializer(serializers.ModelSerializer):
    respuestas = RespuestaSerializer(many=True, required=False, default=[])

    class Meta:
        model = Inspeccion
        fields = '__all__'

    def update(self, instance, validated_data):
        perfil = self.context['request'].user.perfil
        print('aqui 1')
        respuestas_data = validated_data.pop('respuestas')
        print('aqui 2')
        Inspeccion.objects.filter(id=instance.id).update(inspector=perfil, **validated_data)
        inspeccion = Inspeccion.objects.get(id=instance.id)
        print('aqui 3')
        self._borrar_respuestas_inspeccion(inspeccionId=inspeccion.id)
        for respuesta_data in respuestas_data:
            self._crear_respuesta(respuesta_data, inspeccion=inspeccion)
        FotoRespuesta.objects.filter(respuesta=None).delete()
        return validated_data

    def create(self, validated_data):
        respuestas_data = validated_data.pop('respuestas')
        perfil = self.context['request'].user.perfil
        inspeccion = Inspeccion.objects.create(inspector=perfil, **validated_data)

        for respuesta_data in respuestas_data:
            self._crear_respuesta(respuesta_data, inspeccion=inspeccion)
        return inspeccion

    def _borrar_respuestas_inspeccion(self, inspeccionId):
        respuestasPadre = Respuesta.objects.filter(inspeccion__id=inspeccionId)
        print(respuestasPadre)
        respuestasPadre.delete()

    def _crear_respuesta(self, respuesta_data, inspeccion=None, respuesta_cuadricula=None, respuesta_multiple=None):
        fotos_base_data = respuesta_data.pop('fotos_base')
        fotos_reparacion_data = respuesta_data.pop('fotos_reparacion')
        subrespuestas_cuadricula_data = respuesta_data.pop('subrespuestas_cuadricula')
        subrespuestas_multiple_data = respuesta_data.pop('subrespuestas_multiple')
        respuesta = Respuesta.objects.create(inspeccion=inspeccion, respuesta_cuadricula=respuesta_cuadricula,
                                             respuesta_multiple=respuesta_multiple,
                                             **respuesta_data)
        print('aqui')
        for foto_base_data in fotos_base_data:
            self._asociar_foto_base(respuesta, foto_base_data)
        for foto_reparacion_data in fotos_reparacion_data:
            self._asociar_foto_reparacion(respuesta, foto_reparacion_data)
        for subrespuesta_data in subrespuestas_cuadricula_data:
            self._crear_respuesta(subrespuesta_data, respuesta_cuadricula=respuesta)
        for subrespuesta_data in subrespuestas_multiple_data:
            self._crear_respuesta(subrespuesta_data, respuesta_multiple=respuesta)
        return respuesta.id

    def _asociar_foto_base(self, respuesta, foto):
        foto.tipo = FotoRespuesta.TiposDeFoto.base
        foto.respuesta = respuesta
        foto.save()
        respuesta.fotos.add(foto)

    def _asociar_foto_reparacion(self, respuesta, foto):
        foto.tipo = FotoRespuesta.TiposDeFoto.reparacion
        foto.respuesta = respuesta
        foto.save()
        respuesta.fotos.add(foto)


class SubirFotosSerializer(serializers.Serializer):
    fotos = serializers.ListField(child=serializers.ImageField())
    print(fotos)
    class Meta:
        fields = ['fotos']

    def save(self):
        ModelClass = self.Meta.model
        fotos = self.validated_data['fotos']
        print(fotos)
        # storage = FileSystemStorage(location=Path(settings.MEDIA_ROOT) / 'fotos_cuestionarios')
        # name = storage.save(name, content, max_length=self.field.max_length)
        # new_names = {foto.name: storage.save(self.generar_filename(foto.name), foto.file) for foto in fotos}
        new_names = {foto.name: ModelClass._default_manager.create(foto=foto).id for foto in fotos}
        return new_names

    # def generar_filename(self, name: str) -> Path:
    #     file_root, file_ext = os.path.splitext(name)
    #     return Path(f'{get_random_string(7)}{file_ext}')


class SubirFotosCuestionarioSerializer(SubirFotosSerializer):
    class Meta(SubirFotosSerializer.Meta):
        model = FotoCuestionario


class SubirFotosInspeccionSerializer(SubirFotosSerializer):
    class Meta(SubirFotosSerializer.Meta):
        model = FotoRespuesta
