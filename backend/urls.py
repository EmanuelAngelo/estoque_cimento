"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from django.views.static import serve

from backend import settings


def _serve_frontend_index(_request):
    index_path = settings.FRONTEND_DIST_DIR / 'index.html'
    if not index_path.exists():
        raise Http404('Frontend dist não encontrado. Rode o build do frontend.')
    return FileResponse(index_path.open('rb'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('cimento.urls')),
]


if settings.DESKTOP_MODE:
    # Arquivos estáticos do Vite build (normalmente /assets/...) em modo desktop
    assets_dir = settings.FRONTEND_DIST_DIR / 'assets'
    urlpatterns += [
        path('assets/<path:path>', serve, {'document_root': str(assets_dir)}),
        # arquivos na raiz (ex: favicon.ico)
        path('favicon.ico', serve, {'document_root': str(settings.FRONTEND_DIST_DIR), 'path': 'favicon.ico'}),
        # SPA fallback: qualquer rota que não seja /api ou /admin
        re_path(r'^(?!api/|admin/).*$' , _serve_frontend_index),
    ]
