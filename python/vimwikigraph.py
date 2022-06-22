import configargparse
import networkx as nx
import numpy as np
import os
import re


class VimwikiGraph:

# {{{ Private
    def __init__(self, root_dir:str, file_extensions:list=['wiki'], graph_name:str='vimwikigraph', **args):
        self.graph = nx.DiGraph(name=graph_name)
        self.root_dir = root_dir
        self.file_extensions = file_extensions
        self.lines = dict()
        node_dict = self.__create_nodes()
        self.__parse_and_add_edges(node_dict)
        

    def __normalize_path(self, root, link):
        if re.match(r'https?://', link):
            link = re.sub(r'.*:/+', '', link)
            link = re.sub(r'/.*', '', link)
            return link
        if re.match(f'file:/', link):
            link = re.sub(r'.*:/+', '', link)
            link = re.sub(r'.*/', '', link)
            return link
        path = os.path.join(root, link)
        path = re.sub(r':', '', path)
        if not path.endswith(".wiki"):
            path += ".wiki"
        return re.sub(r'[^/]+/\.\./', '', path)


    def __resolve_relative_path(self, path):
        if path[0] == '/':
            return path
        return os.path.join(self.root_dir, path)


    def __create_nodes(self):
        node_dict = dict()
        for root, dir, files in os.walk(self.root_dir):
            for file in files:
                split = file.split('.')
                if split[-1] in self.file_extensions:
                    name = os.path.join(root, file)
                    node_dict[name] = root
                    self.graph.add_node(name, label='.'.join(split[:-1]))
        return node_dict


    def __parse_tags(self, lines):
        tags = list()
        try:
            line = lines[0]
            if re.match(r':(\w+:)+', line):
                tags = line.strip().split(':')
                tags = [tag for tag in tags if tag]
        finally:
            return tags


    def __parse_and_add_edges(self, node_dict):
        for name, root in node_dict.items():
            with open(name, 'r') as f:
                lines = f.readlines()
            self.lines[name] = lines
            self.graph.nodes[name]['tags'] = self.__parse_tags(lines)
            for line in lines:
                links = re.findall(r'\[\[([^#|\[\]]+)(#[^|\[\]]*)?(|[^\]]*)?\]\]', line)
                for link in links:
                    child_node = self.__normalize_path(root, link[0])
                    self.graph.add_edge(name, child_node)
# }}}


# {{{ Utility
    @staticmethod
    def parse():
        """
        Static method to parse options from command line or config file.
        """
        parser = configargparse.ArgParser(default_config_files=['~/.config/vimwikigraph.conf'])
        parser.add('-p', '--root_dir', required=True, help='path to vimwiki directory')
        parser.add('-e', '--file_extensions', nargs='+', default=['wiki'], help='allowed file extensions')
        parser.add('-n', '--graph_name', default='vimwikigraph', help='name of resulting output files')
        parser.add('-r', '--regexes', nargs='*', default=[], help='additional regexes whose matches will be added to the node labels')
        parser.add('-t', help='tags to filter the wiki')
        options = vars(parser.parse_args())
        return options
# }}}


# {{{ Output
    def write_dot(self, name:str=None):
        """
        Writes the current graph to name.dot.

        Args:
            name: Name of the resulting file.
        """
        if not name:
            name = self.graph.name
        PG = nx.drawing.nx_pydot.to_pydot(self.graph)
        PG.set_rankdir('LR')
        PG.write_raw(f"{name}.dot")


    def write_png(self, name:str=None):
        """
        Writes the current graph to name.png.

        Args:
            name: Name of the resulting file.
        """
        if not name:
            name = self.graph.name
        PG = nx.drawing.nx_pydot.to_pydot(self.graph)
        PG.set_rankdir('LR')
        PG.write_png(f"{name}.png")
# }}}


# {{{ Graph Operations
    def add_attribute_by_regex(self, regex, attribute:list, value:list):
        """
        Add attributes with the corresponding values to documents whose contents is matched by the 
        specified regex.

        Args:
            regex (str)
            attribute (list): list of graphviz attribute names
            value (list): list of corresponding values
        """
        try:
            for node in self.graph.nodes:
                lines = self.lines.get(node)
                if lines:
                    for line in lines:
                        if re.search(regex, line):
                            for attr,val in zip(attribute, value):
                                self.graph.nodes[node][attr] = val
                            break
        except Exception as e:
            print(e)
        finally:
            return self
        

    def weight_attribute(self, attribute:str='fontsize', min_val:int=20, max_val:int=100):
        """
        Adds and scales a DOC attribute according to a node's scaled betweenness centrality.
        It will assign the maximum value to the node with the highest betweenness centrality.

        Args:
            attribute: The attribute to add and scale.
            min_val: Minimum value.
            max_val: Maximum value.
        """
        try:
            exponent = np.log(max_val)/np.log(min_val)
            centrality = nx.betweenness_centrality(self.graph)
            max_centrality = max(centrality.values())
            if not max_centrality:
                return self
            for key,value in centrality.items():
                val = max(min((min_val*value/max_centrality)**exponent, max_val), min_val)
                self.graph.nodes[key][attribute] = val
        except Exception as e:
            print(e)
        finally:
            return self


    def filter_nodes_by_tag(self, filter_tags:list):
        """
        Filters nodes by 'filter_tags'. All nodes that do not contain one of the tags in
        'filter_tags' will be removed. Only the first line of every document that has the
        following structure: ":tag1:tag2:tag3:" is considered to be a tag line.

        Args:
            filter_tags (list): List of tags.
        """
        try:
            nodes_to_remove = list()
            for node in self.graph.nodes:
                remove_node = True
                tags = self.graph.nodes[node].get('tags')
                if tags:
                    for tag in tags:
                        if tag in filter_tags:
                            remove_node = False
                            break
                if remove_node:
                    nodes_to_remove.append(node)
            self.graph.remove_nodes_from(nodes_to_remove)
        except Exception as e:
            print(e)
        finally:
            return self


    def collapse_children(self, node:str, depth:int=1):
        """
        All child nodes will be collapsed into this node. Edges from and to children
        will go to the parent instead.

        Args:
            node (str): Full or relative path of a vimwiki document.
            depth (int): Number of levels to contract. Setting depth to a high value
                will remove all of the node's children
        """
        try:
            node = self.__resolve_relative_path(node)
            children = nx.dfs_successors(self.graph, node, depth)
            for child in np.concatenate(list(children.values())):
                nx.contracted_nodes(self.graph, node, child, self_loops=False, copy=False)
            del self.graph.nodes[node]['contraction']
        except Exception as e:
            print(e)
        finally:
            return self


    def extend_node_label(self, regexes:list, join_str:str='\n'):
        """
        Add additional information to node labels.

        Args:
            regexes (list): list of regexes to match data in the node's corresponding documents
            join_str (str): a string or character used to join any matches
        """
        try:
            for node in self.graph.nodes:
                lines = self.lines[node]
                all_matches = list()
                for regex in regexes:
                    for line in lines:
                        matches = re.findall(regex, line)
                        all_matches.extend(matches)
                label = self.graph.nodes[node]['label']
                label = f'"{label}{join_str}{join_str.join(all_matches)}"'
                self.graph.nodes[node]['label'] = label
        except Exception as e:
            print(e)
        finally:
            return self
# }}}



if __name__ == "__main__":
    options = VimwikiGraph.parse()
    vimwikigraph = VimwikiGraph(**options)
    
    tag = options.get('t')
    regexes = options.get('r')
    if tag:
        vimwikigraph = vimwikigraph.filter_nodes_by_tag(tag)
    if regexes:
        vimwikigraph = vimwikigraph.extend_node_label(regexes)
    vimwikigraph.weight_attribute().write_png()
