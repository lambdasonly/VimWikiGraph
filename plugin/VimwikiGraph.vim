if !has("python3")
    echo "vim has to be compiled with +python3 to run this"
    finish
endif

if exists('g:vimwiki_graph_plugin_loaded')
    finish
endif

"{{{ Definitions
let g:vimwiki_collapse_nodes =
    \ get( g:, 'vimwiki_collapse_nodes', ['diary/diary.wiki'] )

let g:vimwiki_weight_attribute =
    \ get( g:, 'vimwiki_weight_attribute', 1 )

let g:vimwiki_graph_name =
    \ get( g:, 'vimwiki_graph_name', '/tmp/vimwikigraph' )

let g:vimwiki_highlight_attributes =
    \ get( g:, 'vimwiki_highlight_attributes', ['style', 'color'] )

let g:vimwiki_highlight_values =
    \ get( g:, 'vimwiki_highlight_values',  ['filled', 'red'] )
"}}}

let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')
py3 << EOF
import sys
from os.path import normpath, join
import vim
import copy
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
from vimwikigraph import VimwikiGraph
graph = VimwikiGraph(root_dir=vim.eval('g:vimwiki_root_dir'))
EOF

function! VimwikiGraph#BuildGraph()
  py3 graph = VimwikiGraph(root_dir=vim.eval('g:vimwiki_root_dir'))
endfunction
command! VimWikiBuildGraph call VimwikiGraph#BuildGraph()

function! VimwikiGraph#GenerateGraph(highlight_regex, data_regex, ...)
  py3 graph_copy = copy.deepcopy(graph)
  for node in g:vimwiki_collapse_nodes
    py3 graph_copy = graph_copy.collapse_children(vim.eval('node'))
  endfor
  if a:0 > 0
    py3 graph_copy = graph_copy.filter_nodes(vim.eval('a:000'))
  endif
  if a:highlight_regex != v:none
    py3 graph_copy = graph_copy.add_attribute_by_regex([vim.eval('a:highlight_regex')],
      \ vim.eval('g:vimwiki_highlight_attributes'), vim.eval('g:vimwiki_highlight_values'))
  endif
  if a:data_regex != v:none
    let data_regex = [a:data_regex]
    py3 graph_copy = graph_copy.extend_node_label(vim.eval('data_regex'))
  endif
  if g:vimwiki_weight_attribute
    py3 graph_copy = graph_copy.weight_attribute()
  endif
  py3 graph_copy.write(vim.eval('g:vimwiki_graph_name'))
  call system('xdg-open ' . g:vimwiki_graph_name . '.png &')
endfunction
command! -nargs=* VimWikiGenerateGraph call VimwikiGraph#GenerateGraph(v:none, v:none, <f-args>)
command! -nargs=* VimWikiGenerateGraphC call VimwikiGraph#GenerateGraph(<f-args>)

let g:vimwiki_graph_plugin_loaded = 1
