import tomllib
import os

class Recipie:
    def __init__(self, title='', servings='', tags=''):
        self.title=title
        self.servings=servings
        self.tags=tags
        
        self._current_node=None
        self.nodes=[]
        self.depth=0
        self.data={}
    
    def __str__(self):
        if self.servings:
            s = f'{self.title} - Serves: {self.servings}'
        else:
            s = self.title
            return s
        
    def __iter__(self):
        for node in self.nodes:
            for n in node:
                yield n
        
    def print(self):
        for n in self.nodes:
            n.print()
        
    
    def add_step(self, inst: str, indent: int):
        n = Node(inst)
        if self._current_node is None:
            self.nodes.append(n)
        else:    
            while self._current_node.depth >= indent and self._current_node.parent is not None:
                self._current_node = self._current_node.parent
                    
            if self._current_node.depth < indent:
                depth = self._current_node.add(n)
                self.depth = max( self.depth, depth )
            else:
                self.nodes.append(n)
        
        self._current_node = n
        
    def get_leaf_nodes(self):
        nodes = []
        for n in self.nodes:
            nodes += n.get_leaf_nodes()
        return nodes
            
    def get_url(self):
        return (recipie.title.replace(' ', '_') + '.html').lower()

class Node:
    def __init__(self, instruction: str):
        self.INDENT = 2
        self.depth = 0
        self.inst = instruction
        self.children=[]
        self.parent=None
        self.printed=False
        
    def __str__(self):
        return ' '*self.INDENT*self.depth + self.inst

    def get_leaf_nodes(self):
        nodes = []
        if len(self.children) == 0:
            nodes += [self]
        else:
            for n in self.children:
                temp = n.get_leaf_nodes()
                nodes += temp
        return nodes
        
    def print(self):
        print(self)
        for n in self.children:
            n.print()
        
    def add(self, node):
        self.children.append(node)
        node.depth = self.depth + 1
        node.parent=self
        return node.depth
    
    def count(self):
        if len(self.children) == 0:
            count = 1
        else:
            count = 0
            
        for n in self.children:
            count += n.count()
        return(count)

def load(name):
    with open(name, 'rb') as f:
        data = tomllib.load(f)
    recipie = Recipie(title = os.path.basename(name).split('.')[0].replace('_',' ').title(), servings = data.pop('servings'), tags = data.pop('tags'))
    for line in data.pop('recipie').split('\n'):
        indent = len(line) - len(line.lstrip())
        recipie.add_step(line.strip(), indent)
    recipie.data = data
    return recipie

def output_html(recipie, directory):
    name = recipie.get_url()
    with open(directory + '/' + name, 'w') as f:
        f.write('<style>table, th, td { padding-left: 5px; padding-right: 5px; border: 1px solid black; border-collapse: collapse; } </style>')
        f.write(f'<h1>{recipie.title}</h1>')
        f.write('<table>')
        f.write(f'<td colspan="{1+recipie.depth}", style="text-align: center;"><b>Servings:</b> {recipie.servings}</td>')
        for n in recipie.get_leaf_nodes():
            if len(n.inst) > 0:
                f.write('<tr>')
                f.write(f'<td colspan="{1+recipie.depth-n.depth}">{n.inst}</td>')
                while n.parent is not None and n.parent.printed is False:
                    n = n.parent
                    f.write(f'<td rowspan="{n.count()}">{n.inst.replace(',',',<br>')}</td>')
                    n.printed = True
                f.write('</tr>')
        f.write('</table>')

        for k, v in recipie.data.items():
            f.write(f'<h4>{k.title()}:</h4>{v}')
            
        f.write('<br><b>Tags:</b>')
        for tag in recipie.tags.split(','):
            tag = tag.strip()
            f.write(f' <a href="./index.html#{tag.lower()}">{tag}</a>')
                
recipies = []
                
for file in os.listdir('./inputs'):
    recipie = load('./inputs/'+file)
    output_html(recipie, './outputs')
    recipies.append(recipie)
    
tags = {}
for recipie in recipies:
    for tag in recipie.tags.split(','):
        tag = tag.strip()
        if tag in tags:
            tags[tag].append(recipie.get_url())
        else:
            tags[tag] = [recipie.get_url()]


with open( './outputs/index.html', 'w') as f:
    for k in sorted(tags.keys()):
        f.write(f'<h3 id="{k.lower()}">{k}</h3>')
        f.write('<ul>')
        for file in tags[k]:
            f.write(f'<li><a href="./{file.lower()}">{file.split('.')[0].title()}</a></li>')
        f.write('</ul>')
            