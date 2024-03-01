import rest_framework.urls
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from rest_framework import routers
from rest_framework.authtoken import views as token_views

from inspecciones import views_api

router = routers.DefaultRouter()
# los que declaran basename es porque sobreescriben el get_queryset, para filtrar por ejemplo
router.register(r'etiquetas-activos', views_api.EtiquetaJerarquicaDeActivoViewSet, basename='etiqueta-activos')
router.register(r'etiquetas-preguntas', views_api.EtiquetaJerarquicaDePreguntaViewSet, basename='etiqueta-preguntas')
router.register(r'users', views_api.UserViewSet, basename='user')
router.register(r'organizaciones', views_api.OrganizacionViewSet)
router.register(r'activos', views_api.ActivoViewSet, basename='activo')
router.register(r'cuestionarios', views_api.CuestionarioViewSet, basename='cuestionario')
router.register(r'cuestionarios-completos', views_api.CuestionarioCompletoViewSet, basename='cuestionario-completo')
router.register(r'inspecciones-completas', views_api.InspeccionCompletaViewSet, basename='inspeccion-completa')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [
    path('', include((router.urls, 'api'), namespace='api')),
    path('api-auth/', include(rest_framework.urls, namespace='rest_framework')),
    path('api-token-auth/', token_views.obtain_auth_token, name='api-token-auth'),
]

# El siguiente codigo permite ver los links y los names generados
# import pprint
# pprint.pprint(router.get_urls())
