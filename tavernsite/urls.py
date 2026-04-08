from django.urls import path

from game.views import game_view

urlpatterns = [
    path('', game_view, name='game'),
]
