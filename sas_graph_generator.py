import dash  # Импортируем основную библиотеку Dash
from dash import dcc, html, Input, Output, State, callback_context  # Импортируем компоненты Dash
import dash_cytoscape as cyto  # Импортируем библиотеку для работы с графами
import networkx as nx  # Для работы с графами
from flask import Flask  # Импортируем Flask для создания серверного приложения

# Парсинг SAS-кода для извлечения взаимосвязей датасетов.
def parse_sas_code(sas_code):
    lines = sas_code.split('\n')
    datasets = []
    outputs = None

    for line in lines:
        line = line.strip().lower()
        if line.startswith('data '):
            outputs = line.split('data')[1].split(';')[0].strip().split()
        elif line.startswith('set ') or line.startswith('merge '):
            inputs = line.split()[1:]
            join_type = 'merge' if 'merge' in line else 'set'
            if outputs:
                for inp in inputs:
                    datasets.append((inp.strip(';'), outputs[0], join_type))
    return datasets

# Функция для преобразования графа NetworkX в формат Dash Cytoscape.
def generate_cytoscape_elements(datasets, root_node="raw_data"):
    graph = nx.DiGraph()
    for dataset in datasets:
        source, target, join_type = dataset
        graph.add_edge(source, target, join_type=join_type)

    elements = []

    # Добавляем узлы.
    for node in graph.nodes:
        elements.append({"data": {"id": node, "label": node}})

    # Добавляем рёбра с разным цветом и стилем.
    for start, end, data in graph.edges(data=True):
        color = "blue" if data["join_type"] == "merge" else "black"
        width = 2 if data["join_type"] == "merge" else 1
        elements.append({"data": {"source": start, "target": end}, "style": {"line-color": color, "width": width}})

    return elements

# Инициализация Dash приложения.
server = Flask(__name__)  # Сервер Flask (необязательно, если нужен только Dash).
app = dash.Dash(__name__, server=server)

app = dash.Dash(__name__)  # Создаем приложение Dash

# Layout приложения
app.layout = html.Div([
    html.Div([
        dcc.Textarea(
            id="sas-code-input",
            placeholder="Вставьте ваш SAS-код сюда...",
            style={"width": "100%", "height": "150px"}
        ),
        dcc.Input(
            id="root-node-input",
            placeholder="Введите корневой узел (по умолчанию 'raw_data')",
            type="text",
            value="raw_data",
            style={"width": "300px", "margin": "10px"}
        ),
        html.Button("Построить граф", id="generate-graph-button", style={"margin": "10px"}),
        html.Button("Очистить", id="clear-graph-button", style={"margin": "10px"}),
    ], style={"margin-bottom": "20px"}),

    html.Div([
        dcc.Input(id="search-node-input", placeholder="Введите название узла для поиска...", type="text", style={"width": "300px"}),
        html.Button("Искать", id="search-node-button", style={"margin-left": "10px"})
    ], style={"margin-bottom": "20px"}),

    html.Div([
        cyto.Cytoscape(
            id="cytoscape-graph",
            layout={"name": "breadthfirst"},  # Иерархия сверху вниз
            style={"width": "100%", "height": "85vh", "background-color": "#808000"},  # Светлый фон
            elements=[],  # Пустые элементы по умолчанию
            stylesheet=[
                {"selector": "node", "style": {"label": "data(label)", "background-color": "red", "color": "white", "text-valign": "center"}},
                {"selector": "edge", "style": {"line-color": "black", "curve-style": "bezier"}},
            ]
        )
    ], style={"height": "100%"})
], style={"height": "100vh"})  # Устанавливаем высоту всего приложения на 100% окна

@app.callback(
    Output("cytoscape-graph", "elements"),
    [Input("generate-graph-button", "n_clicks"),
     Input("clear-graph-button", "n_clicks")],
    [State("sas-code-input", "value"),
     State("root-node-input", "value")],
    prevent_initial_call=True
)
def update_or_clear_graph(generate_clicks, clear_clicks, sas_code, root_node):
    # Определяем, какая кнопка была нажата.
    ctx = callback_context
    if not ctx.triggered:  # Если callback вызван без действия, ничего не делаем.
        return []
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "generate-graph-button":  # Если нажата кнопка "Построить граф".
        if not sas_code:
            return []
        datasets = parse_sas_code(sas_code)
        return generate_cytoscape_elements(datasets, root_node=root_node)

    elif button_id == "clear-graph-button":  # Если нажата кнопка "Очистить".
        return []


# Callback для поиска узлов.
@app.callback(
    Output("cytoscape-graph", "stylesheet"),
    Input("search-node-button", "n_clicks"),
    State("search-node-input", "value"),
    prevent_initial_call=True
)
def highlight_node(n_clicks, search_value):
    if not search_value:
        return [
            {"selector": "node", "style": {"label": "data(label)", "background-color": "red", "color": "white"}},
            {"selector": "edge", "style": {"line-color": "black"}},
        ]

    # Стиль с выделением искомого узла.
    return [
        {"selector": "node", "style": {"label": "data(label)", "background-color": "red", "color": "white"}},
        {"selector": f'node[id = "{search_value}"]', "style": {"background-color": "yellow", "color": "black"}},
        {"selector": "edge", "style": {"line-color": "black"}},
    ]

# Запуск приложения.
if __name__ == "__main__":
    app.run_server(debug=True)
