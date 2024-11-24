import csv
import os
import sys
import requests
from packaging import requirements
from graphviz import Digraph
import time
import unittest
from pathlib import Path

def parse_csv(file_path):
    config = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) != 2:
                raise ValueError("Неверный формат строк в конфигурационном файле")
            config[row[0].strip()] = row[1].strip()
    return config

def get_dependencies(package_name, repo_url):
    url = f'{repo_url}/pypi/{package_name}/json'
    headers = {'User-Agent': 'MyApp/1.0'}
    response = requests.get(url, headers=headers)
    time.sleep(1)
    if response.status_code != 200:
        print(f"Пакет с названием '{package_name}' не найден.")
        return []
    data = response.json()
    requires = data.get('info', {}).get('requires_dist', [])
    if requires is None:
        requires = []
    dependencies = []
    for req in requires:
        print(f"Обработка запроса: {req}")
        try:
            req_obj = requirements.Requirement(req)
            dep_name = req_obj.name
            dependencies.append(dep_name)
        except Exception as e:
            print(f"Не получается найти зависимость: {req}. Ошибка: {e}")
            continue
    return dependencies

def set_dependencies(package, repo_url, visited=None, current_depth=0, max_depth=1):
    if visited is None:
        visited = set()
    dependencies = {}
    if package in visited:
        return dependencies
    visited.add(package)
    print(f"Обработка пакета: {package} (Уровень: {current_depth})")
    if current_depth >= max_depth:
        return dependencies
    deps = get_dependencies(package, repo_url)
    dependencies[package] = deps
    for dep in deps:
        sub_deps = set_dependencies(dep, repo_url, visited, current_depth + 1, max_depth)
        dependencies.update(sub_deps)
    return dependencies

def build_graph(dependencies):
    dot = Digraph(format='png')
    for package, deps in dependencies.items():
        dot.node(package)
        for dep in deps:
            dot.edge(package, dep)
    return dot

def hold_graph(dot, output_path):
    dot.render(filename=output_path, cleanup=True)

def main(config_path):
    config = parse_csv(config_path)
    package_name = config.get("Имя пакета")
    output_dir = config.get("Путь к файлу графа")
    graphviz_path = config.get("Путь к программе для визуализации графов")
    repo_url = config.get("URL репозитория")
    max_depth = int(config.get("Глубина зависимости", 1))  # Default depth is 1

    if not package_name or not output_dir or not graphviz_path or not repo_url:
        print("Не хватает конфигурационных значений в config.csv")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, f"{package_name}_dependencies")

    os.environ['PATH'] += os.pathsep + graphviz_path

    dependencies = set_dependencies(package_name, repo_url, max_depth=max_depth)
    graph = build_graph(dependencies)
    hold_graph(graph, output_path)
    print(f"Граф зависимостей был сохранён в {output_path}.png")

class TestDependencyGraph(unittest.TestCase):
    def test_parse_csv(self):
        config = parse_csv("config.csv")
        self.assertIn("Имя пакета", config)
        self.assertIn("Путь к файлу графа", config)
        self.assertIn("Путь к программе для визуализации графов", config)
        self.assertIn("URL репозитория", config)

    def test_get_dependencies(self):
        dependencies = get_dependencies('requests', 'https://pypi.org')
        self.assertIn('urllib3', dependencies)
        self.assertIn('chardet', dependencies)
        self.assertIn('idna', dependencies)

    def test_set_dependencies(self):
        deps = set_dependencies("pip", "https://pypi.org", max_depth=1)
        self.assertIn("pip", deps)

    def test_build_graph(self):
        dependencies = {"pkgA": ["pkgB", "pkgC"], "pkgB": ["pkgD"]}
        graph = build_graph(dependencies)
        self.assertIn("pkgA", graph.source)
        self.assertIn("pkgB -> pkgD", graph.source)

    def test_hold_graph(self):
        dependencies = {"pkgA": ["pkgB"]}
        graph = build_graph(dependencies)
        hold_graph(graph, "test_output")
        self.assertTrue(Path("test_output.png").exists())
        os.remove("test_output.png")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        unittest.main(argv=[sys.argv[0]])
    else:
        config_path = "config.csv"
        main(config_path)