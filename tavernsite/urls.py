from django.urls import path

from game.views import game_view, handbook_view

urlpatterns = [
    path('', game_view, name='game'),
    path('handbook', handbook_view, name='handbook'),
]
