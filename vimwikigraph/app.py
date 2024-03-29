import json
import re
from flask import Flask, render_template, request
from flask_visjs import VisJS4, Network

from .vimwikigraph import VimwikiGraph


app = Flask(__name__)
app.config.from_envvar('VIMWIKIGRAPH_CONFIG')
VisJS4().init_app(app)


class State:
    instance = None

    def __init__(self, SEP=','):
        self.vimwikigraph = VimwikiGraph(app.config['VIMWIKIDIR'])
        self.filter = app.config.get('DEFAULT_FILTER', [])
        self.highlight = ""
        self.filename_filter = []
        self.collapse = []
        self.SEP = SEP

    @staticmethod
    def get_instance():
        if State.instance is None:
            State.instance = State()
        return State.instance

    def set_form(self, filter, filename_filter, highlight, collapse):
        self.filter = filter.split(self.SEP)
        self.filename_filter = filename_filter.split(self.SEP)
        self.highlight = highlight
        self.collapse = collapse.split(self.SEP)

    def get_graph(self):
        return self.vimwikigraph

    def __str__(self):
        return f'Filter: {self.filter}\nHighlight: {self.highlight}'


@app.route('/', methods=['GET', 'POST'])
def route_index():
    if request.method == 'GET':
        state = State.get_instance()
        rendered = render_template(
            'index.html',
            filter_value=state.SEP.join(state.filter),
            filename_value=state.SEP.join(state.filename_filter),
            highlight_value=state.highlight,
            collapse_value=state.SEP.join(state.collapse),
        )
        return rendered
    if request.method == 'POST':
        state = State.get_instance()
        state.set_form(
            request.form['inptFilter'],
            request.form['inptFileFilter'],
            request.form['inptHighlight'],
            request.form['inptCollapse'],
        )
        rendered = render_template(
            'index.html',
            filter_value=state.SEP.join(state.filter),
            filename_value=state.SEP.join(state.filename_filter),
            highlight_value=state.highlight,
            collapse_value=state.SEP.join(state.collapse),
        )
        return rendered


@app.route('/network')
def network_json():
    state = State.get_instance()
    graph = state.get_graph().reset_graph()
    if state.filter != ['']:
        graph = graph.filter_nodes(state.filter)
    if state.filename_filter != ['']:
        graph = graph.filter_filenames(state.filename_filter)
    if state.collapse != ['']:
        graph = graph.collapse_children(state.collapse)
    if state.highlight:
        attributes = ['color', 'style']
        values = ['red', 'filled']
        graph = graph.add_attribute_by_regex([state.highlight], attributes, values)
    network = Network(
        neighborhood_highlight=True,
        filter_menu=True,
        cdn_resources='remote',
    )
    network.from_nx(graph.graph)
    return network.to_json(max_depth=3)


@app.route('/node', methods=['POST'])
def node_json():
    state = State.get_instance()
    if 'node' in request.json:
        node = request.json['node']
        lines = ''.join(state.vimwikigraph.lines[node])
        # won't find all highlights because the substitution may break subsequent matches
        for f in state.filter:
            lines = re.sub(f, r'<span style="color:red">\g<0></span>', lines)
    else:
        lines = []
    return json.dumps({'text': lines})


@app.route('/reload', methods=['POST'])
def reload():
    state = State.get_instance()
    state.vimwikigraph.reload_graph()
    state.set_form(
        request.form['inptFilter'],
        request.form['inptFileFilter'],
        request.form['inptHighlight'],
        request.form['inptCollapse'],
    )
    rendered = render_template(
        'index.html',
        filter_value=state.SEP.join(state.filter),
        filename_value=state.SEP.join(state.filename_filter),
        highlight_value=state.highlight,
        collapse_value=state.SEP.join(state.collapse),
    )
    return rendered


def create_app():
    return app
