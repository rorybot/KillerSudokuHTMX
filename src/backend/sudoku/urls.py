from django.urls import path
from . import views

urlpatterns = [
    path('', views.sudoku_grid, name='sudoku_grid'),
    path('select/<int:row>/<int:col>/', views.select_cell, name='select_cell'),
    path('enter/', views.enter_number, name='enter_number'),
    path('move/<str:direction>/', views.move_selection, name='move_selection'),
    path('clear/', views.clear_cell, name='clear_cell'),
    path('toggle_note_mode/', views.toggle_note_mode, name='toggle_note_mode'),
]
