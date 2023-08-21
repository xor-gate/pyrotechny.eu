#!/usr/bin/env python311
import pprint

import yaml
import jinja2


class LinksYAMLDB:
	def __init__(self, filename: str):
		with open(filename, "r", encoding="utf-8") as fd:
			self._db = yaml.load(fd, yaml.Loader)
		self._process()

	def _process(self):
		self._categories = {}
		for category in self._db["categories"]:
			category_name = category.capitalize()
			_category = self._categories[category_name] = {}
			_category["links"] = []
			for link in self._db["links"]:
				if category in link["categories"]:
					_category["links"].append(link)

		pprint.pprint(self._categories)

	def generate_categories_page(self):
		env = jinja2.Environment(
			loader=jinja2.FileSystemLoader("data"),
			autoescape=jinja2.select_autoescape()
		)
		tmpl = env.get_template("links-categories-page.md.jinja2")
		data = tmpl.render(categories=self._db["categories"])
		with open("src/content/links/categories.md", "w", encoding="utf8") as fd:
			fd.write(data)

	def _generate_category_page(self, category: str, links: dict):
		env = jinja2.Environment(
			loader=jinja2.FileSystemLoader("data"),
			autoescape=jinja2.select_autoescape()
		)
		tmpl = env.get_template("links-category-page.md.jinja2")
		data = tmpl.render(name=category, links=links)
		with open(f"src/content/links/category/{category}.md", "w", encoding="utf8") as fd:
			fd.write(data)

	def generate_category_pages(self):
		for category in self._categories.keys():
			self._generate_category_page(category, links=self._categories[category]["links"])


links_db = LinksYAMLDB("data/links.yaml")
links_db.generate_categories_page()
links_db.generate_category_pages()
