import json
import os
import re
from flask import Flask, render_template, request
from flask_visjs import VisJS4, Network

from .vimwikigraph import VimwikiGraph
from .vimwikitags import VimwikiTags


app = Flask(__name__)
app.config.from_envvar('VIMWIKIGRAPH_CONFIG')
VisJS4().init_app(app)


class State:
    instance = None

    def __init__(self):
        self.vimwikigraphdir = os.environ.get('VIMWIKIDIR', '')
        if not self.vimwikigraphdir:
            raise ValueError('VIMWIKIDIR environment variable is not set')
        self.vimwikigraph = VimwikiGraph(self.vimwikigraphdir)
        self.vimwikitags = VimwikiTags(self.vimwikigraphdir)
        self.reset_form()
        self.exclude_tags = app.config.get('EXCLUDE_TAGS', [])
        self.n_tags = app.config.get('N_TAGS', 30)
        self.SEP = app.config.get('SEPARATOR', ';')

    def reset_form(self):
        self.filter = app.config.get('DEFAULT_FILTER', [])
        self.invert_filter = app.config.get('DEFAULT_INVERT_FILTER', False)
        self.highlight = app.config.get('DEFAULT_HIGHLIGHT', [])
        self.filename_filter = app.config.get('DEFAULT_FILE_FILTER', [])
        self.invert_filename_filter = app.config.get('DEFAULT_INVERT_FILE_FILTER', False)
        self.collapse = app.config.get('DEFAULT_COLLAPSE', [])

    @staticmethod
    def get_instance():
        if State.instance is None:
            State.instance = State()
        return State.instance

    def set_form(self, filter, invert_filter, filename_filter, invert_file_filter, highlight, collapse):
        self.filter = filter.split(self.SEP)
        self.invert_filter = invert_filter
        self.filename_filter = filename_filter.split(self.SEP)
        self.invert_filename_filter = invert_file_filter
        self.highlight = highlight.split(self.SEP)
        self.collapse = collapse.split(self.SEP)

    def get_graph(self):
        return self.vimwikigraph

    def __str__(self):
        msg = "Filter"
        if self.invert_filter:
            msg += "[X]"
        msg += f": {self.filter}\nFilename filter"
        if self.invert_filename_filter:
            msg += "[X]"
        msg += f": {self.filename_filter}\nHighlight: {self.highlight}"
        return msg


@app.route('/', methods=['GET', 'POST'])
def route_index():
    if request.method == 'GET':
        state = State.get_instance()
        rendered = render_template(
            'index.html',
            filter_value=state.SEP.join(state.filter),
            invert_filter_value=state.invert_filter,
            filename_value=state.SEP.join(state.filename_filter),
            invert_filename_value=state.invert_filename_filter,
            highlight_value=state.SEP.join(state.highlight),
            collapse_value=state.SEP.join(state.collapse),
            sep=state.SEP,
        )
        return rendered
    if request.method == 'POST':
        state = State.get_instance()
        state.set_form(
            request.form['inptFilter'],
            'inptInvertFilter' in request.form,
            request.form['inptFileFilter'],
            'inptInvertFileFilter' in request.form,
            request.form['inptHighlight'],
            request.form['inptCollapse'],
        )
        rendered = render_template(
            'index.html',
            filter_value=state.SEP.join(state.filter),
            invert_filter_value=state.invert_filter,
            filename_value=state.SEP.join(state.filename_filter),
            invert_filename_value=state.invert_filename_filter,
            highlight_value=state.SEP.join(state.highlight),
            collapse_value=state.SEP.join(state.collapse),
            sep=state.SEP,
        )
        return rendered


@app.route('/network')
def network_json():
    state = State.get_instance()
    graph = state.get_graph().reset_graph()
    if state.filename_filter != ['']:
        graph = graph.filter_filenames(state.filename_filter, invert=state.invert_filename_filter)
    if state.filter != ['']:
        graph = graph.filter_nodes(state.filter, invert=state.invert_filter)
    if state.collapse != ['']:
        graph = graph.collapse_children(state.collapse)
    if state.highlight != ['']:
        attributes = ['color', 'style']
        values = ['red', 'filled']
        graph = graph.add_attribute_by_regex(state.highlight, attributes, values)
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
    if request.json and 'node' in request.json:
        node = request.json['node']
        lines = ''.join(state.vimwikigraph.lines[node])
        for highlight in state.highlight:
            lines = re.sub(highlight, r'<span style="background:red">\g<0></span>', lines, flags=re.IGNORECASE)
    else:
        lines = []
    return json.dumps({'text': lines})


@app.route('/reload', methods=['POST'])
def reload():
    state = State.get_instance()
    state.vimwikigraph.reload_graph()
    state.vimwikitags.reload()
    state.set_form(
        request.form['inptFilter'],
        'inptInvertFilter' in request.form,
        request.form['inptFileFilter'],
        'inptInvertFileFilter' in request.form,
        request.form['inptHighlight'],
        request.form['inptCollapse'],
    )
    rendered = render_template(
        'index.html',
        filter_value=state.SEP.join(state.filter),
        invert_filter_value=state.invert_filter,
        filename_value=state.SEP.join(state.filename_filter),
        invert_filename_value=state.invert_filename_filter,
        highlight_value=state.SEP.join(state.highlight),
        collapse_value=state.SEP.join(state.collapse),
        sep=state.SEP,
    )
    return rendered


@app.route('/reset', methods=['GET'])
def reset():
    state = State.get_instance()
    state.reset_form()
    return json.dumps({
        'filter_value': state.SEP.join(state.filter),
        'invert_filter_value': state.invert_filter,
        'filename_value': state.SEP.join(state.filename_filter),
        'invert_filename_value': state.invert_filename_filter,
        'highlight_value': state.highlight,
        'collapse_value': state.SEP.join(state.collapse),
    })


@app.route('/tags', methods=['GET'])
def tags():
    state = State.get_instance()
    count_dict = state.vimwikitags.populate_tags()
    tags = [tag for tag in list(count_dict.keys()) if tag not in state.exclude_tags]
    return json.dumps({'tags': tags[:state.n_tags]})


def create_app():
    return app
