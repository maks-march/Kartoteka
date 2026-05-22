from django.urls import path
from . import views, graphs

urlpatterns = [
    # Главная страница
    path('', views.overview_view, name='overview'),

    # Объекты
    path('objects/', views.object_list_view, name='object_list'),
    path('objects/<int:object_id>/', views.object_detail_view, name='object_detail'),
    path('objects/<int:pk>/edit/', views.object_edit_view, name='object_edit'),
    path('objects/<int:pk>/delete/', views.object_delete_view, name='object_delete'),
    path('objects/create/', views.object_create_view, name='object_create'),
    path('objects/<int:pk>/history/', views.object_history_view, name='object_history'),

    # Классы объектов
    path('classes/', views.class_list_view, name='class_list'),
    path('classes/<int:class_id>/', views.class_detail_view, name='class_detail'),
    path('class-hierarchy/', views.class_hierarchy_view, name='class_hierarchy'),
    path('иерархия-классов/', views.class_hierarchy_view, name='class_hierarchy_alt'),

    # Участники
    path('participants/', views.participant_list_view, name='participant_list'),
    path('participants/grouped/', views.participants_by_type_view, name='participants_by_type'),
    path('participants/<int:participant_id>/', views.participant_detail_view, name='participant_detail'),
    path('participants/<int:pk>/edit/', views.participant_edit_view, name='participant_edit'),
    path('participants/<int:pk>/delete/', views.participant_delete_view, name='participant_delete'),
    path('participants/create/', views.participant_create_view, name='participant_create'),
    path('participants/<int:pk>/history/', views.participant_history_view, name='participant_history'),

    # Вендорские продукты
    path('vendor-products/', views.vendor_product_list_view, name='vendor_product_list'),
    path('vendor-products/<int:product_id>/', views.vendor_product_detail_view, name='vendor_product_detail'),

    # Автоматизированные системы
    path('systems/', views.system_list_view, name='system_list'),
    path('systems/<int:pk>/', views.system_detail_view, name='automated_system_detail'),
    path('systems/<int:pk>/edit/', views.system_edit_view, name='system_edit'),
    path('systems/<int:pk>/delete/', views.system_delete_view, name='system_delete'),
    path('systems/create/', views.system_create_view, name='system_create'),
    path('systems/<int:pk>/history/', views.system_history_view, name='system_history'),

    # Уровни автоматизации
    path('automation-levels/<slug:level_code>/', views.level_detail_view, name='level_detail'),

    # Отчёты и аналитика
    path('reports/automation/', views.automation_report_view, name='automation_report'),

    # Визуализация
    path('graph/', views.graph_view, name='graph'),
    path('graph-pyvis/', graphs.create_graph_view, name='graph_pyvis'),
    path('ownership/', views.ownership_view, name='ownership'),

    # API endpoints
    path('api/objects-by-level/<str:level_code>/', views.api_objects_by_level, name='api_objects_by_level'),
    path('api/graph-data/', views.graph_data_api, name='graph-data-api'),

    # Импорт и экспорт
    path('export/', views.export_data, name='export_data'),
    path('import/', views.import_data, name='import_data'),
    path('export-import/', views.export_import_page, name='export_import_page'),

    path('user-guide/', views.user_guide_view, name='user_guide'),
]
