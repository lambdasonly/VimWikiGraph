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
from os.path import normpath, join
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
from vimwikigraph import VimwikiGraph
EOF


function! VimwikiGraph#GenerateGraph(data_regex, highlight_regex, ...)
  py3 graph = VimwikiGraph(root_dir=vim.eval('g:vimwiki_root_dir'))
  for node in g:vimwiki_collapse_nodes
    py3 graph = graph.collapse_children(vim.eval('node'))
  endfor
  if a:0 > 0
    py3 graph = graph.filter_nodes(vim.eval('a:000'))
  endif
  if a:highlight_regex != v:none
    py3 graph = graph.add_attribute_by_regex([vim.eval('a:highlight_regex')],
      \ vim.eval('g:vimwiki_highlight_attributes'), vim.eval('g:vimwiki_highlight_values'))
  endif
  if a:data_regex != v:none
    let data_regex = [a:data_regex]
    py3 graph = graph.extend_node_label(vim.eval('data_regex'))
  endif
  if g:vimwiki_weight_attribute
    py3 graph = graph.weight_attribute()
  endif
  py3 graph.write(vim.eval('g:vimwiki_graph_name'))
  call system('xdg-open ' . g:vimwiki_graph_name . '.png &')
endfunction
command! -nargs=* VimWikiGenerateGraph   call VimwikiGraph#GenerateGraph(v:none, v:none, <f-args>)
command! -nargs=* VimWikiGenerateGraphC  call VimwikiGraph#GenerateGraph(v:none, <f-args>)
command! -nargs=* VimWikiGenerateGraphCC call VimwikiGraph#GenerateGraph(<f-args>)


function! VimwikiGraph#AdjacencyGraph(depth)
  py3 graph = VimwikiGraph(root_dir=vim.eval('g:vimwiki_root_dir'))
  py3 graph.remove_nonadjacent_nodes(vim.current.buffer.name, int(vim.eval('a:depth'))).write(vim.eval('g:vimwiki_graph_name'))
  call system('xdg-open ' . g:vimwiki_graph_name . '.png &')
endfunction
command! -nargs=1 VimWikiGenerateAdjacencyGraph call VimwikiGraph#AdjacencyGraph(<f-args>)


let g:vimwiki_graph_plugin_loaded = 1
