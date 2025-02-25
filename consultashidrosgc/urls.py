from django.urls import path 
from .views import consultar, error_404, error_403, error_500
from django.conf.urls import handler404, handler403, handler500



urlpatterns = [
      path('', consultar, name='consultar'),  #
]



handler404 = error_404
handler403 = error_403
handler500 = error_500