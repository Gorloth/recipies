import tomllib
import os
import re

class Recipe:
    def __init__(self, title='', servings='', tags='', flavor=''):
        self.title=title
        self.servings=servings
        self.tags=tags.title()
        self.flavors = flavor
        
        self._current_node=None
        self.nodes=[]
        self.depth=0
        self.data={}
        self.used_in=[]
    
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
        return (recipe.title.replace(' ', '_') + '.html').lower()
        
    def get_refs(self):
        nodes = self.get_leaf_nodes()
        refs = []
        for node in nodes:
            refs = refs + node.refs
        return(refs)

class Node:
    def __init__(self, instruction: str):
        self.INDENT = 2
        self.depth = 0
        self.inst = instruction
        self.children=[]
        self.parent=None
        self.printed=False
        self.refs = re.findall(r'\*(.*?)\*', self.inst)
        
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
        
        
    def get_html_inst(self):
        html = self.inst
        for ref in self.refs:
            html = html.replace('*'+ref+'*', format_link(ref))
        return(html)
    
def format_link(link):
    return(f'<a href="./{link.lower().replace(' ','_')}.html">{link}</a>')

def load(name):
    with open(name, 'rb') as f:
        data = tomllib.load(f)
    if 'flavors' in data:
        flavor = data.pop('flavors')
    else:
        flavor = None
    recipe = Recipe(title = os.path.basename(name).split('.')[0].replace('_',' ').title(), servings = data.pop('servings'), tags = data.pop('tags'), flavor = flavor)
    for line in data.pop('recipe').split('\n'):
        indent = len(line) - len(line.lstrip())
        recipe.add_step(line.strip(), indent)
    recipe.data = data
    return recipe

def output_html(recipe, directory):
    name = recipe.get_url()
    with open(directory + '/' + name, 'w') as f:
        f.write('<style>table, th, td { padding-left: 5px; padding-right: 5px; border: 1px solid black; border-collapse: collapse; } </style>\n')
        f.write(f'<title>{recipe.title}</title>\n')
        f.write(f'<h1>{recipe.title}</h1>\n')
        f.write('<table>\n')
        f.write(f'<td colspan="{1+recipe.depth}", style="text-align: center;"><b>Servings:</b> {recipe.servings}</td>\n')
        for n in recipe.get_leaf_nodes():
            if len(n.inst) > 0:
                f.write('<tr>\n')
                if n.parent is None:
                    f.write(f'<td colspan="{1+recipe.depth}", style="text-align: center;"><b>{n.get_html_inst()}</b></td>\n')
                else:
                    f.write(f'<td colspan="{1+recipe.depth-n.depth}">{n.get_html_inst()}</td>\n')
                    while n.parent is not None and n.parent.printed is False:
                        n = n.parent
                        f.write(f'<td rowspan="{n.count()}">{n.get_html_inst().replace(',','<br>')}</td>\n')
                        n.printed = True
                f.write('</tr>\n')
        f.write('</table>\n')

        for k, v in recipe.data.items():
            f.write(f'<h4>{k.title()}:</h4>{v}<br>\n')
            
        f.write('<br><b>Tags:</b>\n')
        for tag in recipe.tags.split(','):
            tag = tag.strip()
            f.write(f' <a href="../index.html#{tag.lower()}">{tag}</a>\n')
            
        if recipe.flavors is not None:
            f.write('<br><b>Flavors:</b>\n')
            for flavor in recipe.flavors.split(','):
                flavor = flavor.strip()
                f.write(f' <a href="../flavor.html#{flavor.lower()}">{flavor.title()}</a>\n')
            
        if len(recipe.used_in) > 0:
            f.write('<br><br><b>Used in:</b>\n')
            text = ''
            for ref in recipe.used_in:
                text += (' ' + format_link(ref) + ',')
            f.write(text[0:-1])
                
recipes = []
                
for file in os.listdir('./inputs'):
    recipe = load('./inputs/'+file)
    recipes.append(recipe)
    
tags = {}
flavors = {}
for recipe in recipes:
    for tag in recipe.tags.split(','):
        tag = tag.strip()
        if tag in tags:
            tags[tag].append(recipe.get_url())
        else:
            tags[tag] = [recipe.get_url()]
            
    if recipe.flavors is not None:
        for flavor in recipe.flavors.split(','):
            flavor = flavor.strip()
            if flavor in flavors:
                flavors[flavor].append(recipe.get_url())
            else:
                flavors[flavor] = [recipe.get_url()]
    
    
    for ref in recipe.get_refs():
        for other in recipes:
            if other.title == ref:
                other.used_in.append(recipe.title)
        

for recipe in recipes:
    output_html(recipe, './outputs')

with open( './index.html', 'w') as f:
    for k in sorted(tags.keys()):
        f.write(f'<h3 id="{k.lower()}">{k}</h3>\n')
        f.write('<ul>\n')
        for file in tags[k]:
            f.write(f'<li><a href="./outputs/{file.lower()}">{file.split('.')[0].title()}</a></li>\n')
        f.write('</ul>\n')
            
with open( './flavor.html', 'w') as f:
    for k in sorted(flavors.keys()):
        f.write(f'<h3 id="{k.lower()}">{k}</h3>\n')
        f.write('<ul>\n')
        for file in flavors[k]:
            f.write(f'<li><a href="./outputs/{file.lower()}">{file.split('.')[0].title()}</a></li>\n')
        f.write('</ul>\n')
            