- [Intro](#introduction)
- [Screenshots](#screenshots)
- [Usage](#usage guide)
- [Installation](#installation)
- [Commands](#commands)

# Introduction
Vim plugin extension for vimwiki. Creates a directed graph of links between vimwiki files and
allows for various filtering operations.

# Usage Guide
VimWikiGraph currently supports one filtering method and two text extraction/highlighting methods.
Notes can be filtered according to their tags. Tags may only occur in the first line of every note
and are separated by colons ':tag1:tag2:tag3:'. Additionally, nodes can be highlighted and their
labels extended by specifying regexes [see the examples below](#screenshots).

# Screenshots

# Installation
```
Plug 'https://github.com/lambdasonly/VimwikiGraph, { 'for': 'vimwiki', 'do': './install.sh' }
```

# Commands
The internal graph representation is automatically generated upon plugin load. If, upon creating new links or files you want to refresh the graph, you can call 'VimWikiBuildGraph'.

The graph is visualized by calls to either
VimWikiGenerateGraph or VimWikiGenerateGraphC where the former is a more streamlined version that only supports tag filtering.
