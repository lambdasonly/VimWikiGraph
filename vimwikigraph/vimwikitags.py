from ripgrepy import Ripgrepy


class VimwikiTags:

    def __init__(self, root_dir, search_pattern=r'^:((\w+:)+)'):
        self.root_dir = root_dir
        self.search_pattern = search_pattern
        self.search_result = []
        self.count_dict = {}

    def _search(self):
        rg = Ripgrepy(self.search_pattern, self.root_dir)
        matches = rg.no_filename().only_matching().run().as_string
        matches = matches.split(':')
        self.search_result = [m for m in matches if m != '' and m != '\n']

    def _generate_counts_dict(self):
        counts = dict()
        for m in self.search_result:
            if m not in counts:
                counts[m] = 1
            else:
                counts[m] += 1
        self.count_dict = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))

    def _format_dict(self):
        counts_list = list()
        for k, v in self.count_dict.items():
            counts_list.append("* {:<3} {}".format(str(v), k))
        return counts_list

    def populate_tags(self) -> dict:
        if not self.search_result:
            self._search()
        if not self.count_dict:
            self._generate_counts_dict()
        return self.count_dict # type: ignore

    def reload(self):
        del self.search_result, self.count_dict
        self.search_result = []
        self.count_dict = {}
