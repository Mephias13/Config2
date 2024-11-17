import csv
import os
import importlib.metadata
import graphviz
from pathlib import Path
import unittest


def parse_csv(file_path):
    config = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        file = csv.reader(csvfile)
        for line in file:
            if len(line) != 2:
                raise ValueError("Неверный формат строк в конфигурационном файле")
            config[line[0]] = line[1]
    return config


def set_dependencies(package, visited = None):
    if visited is None:
        visited = set()
    dependencies = {}
    if package in visited:
        return dependencies
    visited.add(package)
    try:
        required = importlib.metadata.requires(package)
        dependencies[package] = []
        if required:
            for req in required:
                name_of_req = req.split(';')[0].split('[')[0].strip()
                dependencies[package].append(name_of_req)
                sub_req = set_dependencies(name_of_req, visited)
                dependencies.update(sub_req)
    except importlib.metadata.PackageNotFoundError:
        print(f"Пакет '{package}' не найден.")
    return dependencies


def build_graph(dependencies):
    dot = graphviz.Digraph(format = 'png')
    for package, deps in dependencies.items():
        dot.node(package)
        for dep in deps:
            dot.edge(package, dep)
    return dot


def hold_graph(dot, output_path):
    dot.render(filename=output_path, cleanup=True)


def draw_dependencies(config_path):
    config = parse_csv(config_path)
    package = config.get("Имя пакета")
    output_path = config.get("Путь к файлу графа")
    dependencies = set_dependencies(package)
    graph = build_graph(dependencies)
    hold_graph(graph, output_path)
    print("Граф зависимостей успешно сохранён в", output_path + ".png")


class BasicTests(unittest.TestCase):

    def test_parser(self):
        config = parse_csv("config.csv")
        self.assertIn("Имя пакета", config)
        self.assertIn("Путь к файлу графа", config)

    def test_dependencies(self):
        deps = set_dependencies("pip")
        self.assertIn("pip", deps)

    def test_graph_builder(self):
        dependencies = {"pkgA": ["pkgB", "pkgC"], "pkgB": ["pkgD"]}
        graph = build_graph(dependencies)
        self.assertIn("pkgA", graph.source)
        self.assertIn("pkgB -> pkgD", graph.source)

    def test_save_graph(self):
        dependencies = {"pkgA": ["pkgB"]}
        graph = build_graph(dependencies)
        hold_graph(graph, "test_output")
        self.assertTrue(Path("test_output.png").exists())
        os.remove("test_output.png")


if __name__ == "__main__":
    draw_dependencies("config.csv")
    unittest.main()
