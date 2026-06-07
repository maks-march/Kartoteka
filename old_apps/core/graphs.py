import networkx as nx
from pyvis.network import Network
import json


def build_simple_industrial_graph():
    """Построить простой граф связей из базы данных"""
    from .models import AutomatedSystem, Object, Participant

    G = nx.DiGraph()

    try:
        # Добавляем объекты
        objects = Object.objects.all()
        for obj in objects:
            level_display = obj.get_hierarchy_level_display() if hasattr(obj,
                                                                         'get_hierarchy_level_display') else obj.hierarchy_level

            G.add_node(
                f"object_{obj.id}",
                label=obj.name[:20],
                title=f"{obj.name}\nУровень: {level_display}\nКатегория: {obj.get_category_display()}",
                group="object",
                color="#FF6B6B"
            )

        # Добавляем связи из автоматизированных систем
        systems = AutomatedSystem.objects.select_related(
            'object', 'vendor', 'implementer'
        )

        for system in systems:
            # Вендор
            if system.vendor:
                vendor_node_id = f"vendor_{system.vendor.id}"
                if vendor_node_id not in G:
                    vendor_type = system.vendor.get_participant_type_display() if hasattr(system.vendor,
                                                                                          'get_participant_type_display') else system.vendor.participant_type

                    G.add_node(
                        vendor_node_id,
                        label=system.vendor.name[:15],
                        title=f"{system.vendor.name}\nТип: {vendor_type}",
                        group="vendor",
                        color="#4ECDC4"
                    )

                system_class = system.get_system_class_display() if hasattr(system,
                                                                            'get_system_class_display') else system.system_class

                G.add_edge(
                    vendor_node_id,
                    f"object_{system.object.id}",
                    label="поставляет",
                    title=f"{system_class} v{system.version}",
                    color="#4ECDC4"
                )

            # Внедренец
            if system.implementer:
                implementer_node_id = f"implementer_{system.implementer.id}"
                if implementer_node_id not in G:
                    impl_type = system.implementer.get_participant_type_display() if hasattr(system.implementer,
                                                                                             'get_participant_type_display') else system.implementer.participant_type

                    G.add_node(
                        implementer_node_id,
                        label=system.implementer.name[:15],
                        title=f"{system.implementer.name}\nТип: {impl_type}",
                        group="implementer",
                        color="#45B7D1"
                    )

                system_class = system.get_system_class_display() if hasattr(system,
                                                                            'get_system_class_display') else system.system_class

                G.add_edge(
                    implementer_node_id,
                    f"object_{system.object.id}",
                    label="внедряет",
                    title=f"{system_class} v{system.version}",
                    color="#45B7D1"
                )

        # Связи иерархии объектов
        for obj in objects:
            if obj.parent:
                G.add_edge(
                    f"object_{obj.parent.id}",
                    f"object_{obj.id}",
                    label="включает",
                    title=f"Иерархия: {obj.parent.name} → {obj.name}",
                    color="#3366cc"
                )

        return G

    except Exception as e:
        print(f"Ошибка при построении графа: {e}")
        import traceback
        traceback.print_exc()
        return nx.DiGraph()


def save_graph_to_html():
    """
    Сохранить граф как HTML файл и вернуть путь к нему
    """
    G = build_simple_industrial_graph()

    if G.number_of_nodes() == 0:
        return None, "Нет данных для построения графа"

    net = Network(
        height="600px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#ffffff",
        font_color="#2c3e50"
    )

    # Настройки визуализации
    net.from_nx(G)

    # Настройки для лучшего отображения
    net.set_options("""
    var options = {
        "nodes": {
            "font": {
                "size": 14,
                "face": "Tahoma"
            },
            "borderWidth": 2,
            "shadow": true
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "font": {
                "size": 12,
                "align": "middle"
            },
            "smooth": {
                "type": "continuous"
            }
        },
        "physics": {
            "enabled": true,
            "stabilization": {
                "enabled": true,
                "iterations": 100
            },
            "solver": "forceAtlas2Based"
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "navigationButtons": true
        }
    }
    """)

    # Сохраняем в файл
    html_path = "core/old_templates/core/graph_visualization.html"
    try:
        net.save_graph(html_path)
        return html_path, f"Граф сохранен. Узлов: {G.number_of_nodes()}, связей: {G.number_of_edges()}"
    except Exception as e:
        return None, f"Ошибка сохранения: {e}"


def get_graph_statistics():
    """Получить статистику графа"""
    G = build_simple_industrial_graph()

    if G.number_of_nodes() == 0:
        return {"error": "Граф пустой"}

    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": {},
        "most_connected_nodes": []
    }

    # Считаем типы узлов
    for node, data in G.nodes(data=True):
        node_type = data.get('group', 'unknown')
        stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1

    # Находим наиболее связанные узлы
    degrees = dict(G.degree())
    sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]

    for node_id, degree in sorted_degrees:
        node_data = G.nodes[node_id]
        stats["most_connected_nodes"].append({
            "name": node_data.get('label', node_id),
            "degree": degree,
            "type": node_data.get('group', 'unknown')
        })

    return stats


def get_graph_data_for_template():
    """Получить данные графа для передачи в шаблон Django (для vis-network)"""
    G = build_simple_industrial_graph()

    nodes = []
    edges = []

    if G.number_of_nodes() == 0:
        return {"nodes": [], "edges": []}

    # Преобразуем узлы
    for node_id, data in G.nodes(data=True):
        nodes.append({
            'id': node_id,
            'label': data.get('label', node_id),
            'title': data.get('title', ''),
            'group': data.get('group', 'unknown'),
            'color': data.get('color', '#97C2FC'),
            'shape': 'dot',
            'size': 20
        })

    # Преобразуем связи
    for from_node, to_node, data in G.edges(data=True):
        edges.append({
            'from': from_node,
            'to': to_node,
            'label': data.get('label', ''),
            'title': data.get('title', ''),
            'color': data.get('color', '#848484'),
            'arrows': 'to',
            'width': 2
        })

    return {
        'nodes': nodes,
        'edges': edges
    }


def create_graph_view(request):
    """
    Вьюха для отображения графа через pyvis
    """
    from django.shortcuts import render
    from django.conf import settings
    import os

    # Сохраняем граф
    html_path, message = save_graph_to_html()

    if html_path:
        # Читаем сохраненный HTML
        full_path = os.path.join(settings.BASE_DIR, html_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                graph_html = f.read()
        except:
            graph_html = f"<p>Ошибка чтения файла: {message}</p>"
    else:
        graph_html = f"<p>{message}</p>"

    # Получаем статистику
    stats = get_graph_statistics()

    return render(request, 'core/graph_pyvis.html', {
        'graph_html': graph_html,
        'stats': stats
    })