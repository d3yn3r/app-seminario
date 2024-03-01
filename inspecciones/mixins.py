from django.http import Http404
from rest_framework import status, serializers
from rest_framework.request import clone_request
from rest_framework.response import Response
from rest_framework.settings import api_settings


class AbsoluteLinksMixin(object):
    def image_to_representation(self, value):
        if not value:
            return None

        use_url = getattr(self, 'use_url', api_settings.UPLOADED_FILES_USE_URL)
        if use_url:
            try:
                url = value.url
            except AttributeError:
                return None
            request = self.context.get('request', None)
            if request is not None:
                return request.build_absolute_uri(url)
            return url

        return value.name


class CreateAsUpdateMixin(object):
    def create(self, request, *args, **kwargs):
        self.kwargs[self.lookup_url_kwarg] = request.data.get(self.lookup_url_kwarg)
        instance = self.get_object_or_none()
        if instance is None:
            return super().create(request, *args, **kwargs)
        else:
            return super().update(request, *args, **kwargs)

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            return None


class PutAsCreateMixin(object):
    """
    The following mixin class may be used in order to support
    PUT-as-create behavior for incoming requests.
    """

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object_or_none()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if instance is None:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_create(self, serializer):
        if not hasattr(self, 'lookup_fields'):
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            lookup_value = self.kwargs[lookup_url_kwarg]
            extra_kwargs = {self.lookup_field: lookup_value}
        else:
            # set kwargs for additional fields
            extra_kwargs = {
                field: self.kwargs[field]
                for field in self.lookup_fields if self.kwargs[field]
            }
        serializer.save(**extra_kwargs)

    def perform_update(self, serializer):
        serializer.save()

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                # For PUT-as-create operation, we need to ensure that we have
                # relevant permissions, as if this was a POST request. This
                # will either raise a PermissionDenied exception, or simply
                # return None.
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                # PATCH requests where the object does not exist should still
                # return a 404 response.
                raise


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    fuente: https://www.django-rest-framework.org/api-guide/serializers/#example
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)