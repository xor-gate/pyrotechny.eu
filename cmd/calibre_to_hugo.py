# https://manual.calibre-ebook.com/db_api.html
import os
import json
import copy
import shutil
import pathlib
import hashlib
import calibre.library

import config

class CalibreLibrary: pass

class CalibreLibraryBook:
	_db: CalibreLibrary

	id: int
	title: str
	authors: str
	filepath: str
	filehash: str
	filename: str
	cover: str

	def __init__(self, db: CalibreLibrary):
		self._db = db
		self.cover = None
		self.filehash = None

	""" Hash the filepath SHA256 to hex string """
	def hash(self) -> str:
		if not self.filehash:
			self.filehash = hashlib.sha256(self.filepath.encode("utf8")).hexdigest()

		return self.filehash

	""" Get book properties for JSON serialize """
	def to_json(self):
		data = {}
		for key in list(self.__dict__.keys()):
			if key.startswith("_"):
				continue
			data[key] = self.__dict__[key]

		return data

	""" Generate the ebook filename based on the ebook file hash """
	def ebook_filename(self) -> str:
		filehash = self.hash()
		ext = pathlib.Path(self.filepath).suffix
		self.filename = f"{filehash}{ext}"
		return self.filename
		
	""" Save the ebook from the calibre library to the path """
	def ebook_save(self, path: str) -> str:
		filepath = os.path.join(path, self.ebook_filename())

		if os.path.exists(filepath):
			return

		print(f"COPY {self.filepath} -> {filepath}")
		shutil.copyfile(self.filepath, filepath)
		return filepath

	""" Save the ebook cover to the path """
	def cover_save(self, path: str) -> str:
		filehash = self.hash()
		if not self.cover:
			cover_tmpfile = self._db.cover(self.id, as_path=True)
			cover_ext = pathlib.Path(cover_tmpfile).suffix
			self.cover = os.path.join(path, f"{filehash}{cover_ext}")
			os.rename(cover_tmpfile, self.cover)
			print(f"SAVE COVER {self.cover}")

		return self.cover

class CalibreLibrary:
	def __init__(self, library_path: str):
		# First open the Calibre library and get a list of the book IDs
		self._db = calibre.library.db(library_path).new_api

	def books(self) -> 'list[CalibreLibraryBook]':
		books = []
		book_ids = self._db.all_book_ids()

		for book_id in book_ids:
			book = CalibreLibraryBook(self._db)

			book.id = book_id

			# TODO check loaded state with state of calibre based on book.id
			#      hashing takes way to long...

			book.title = self._db.field_for("title", book.id)
			book.authors = self._db.field_for("authors", book.id)

			# Select only first ebook format 
			formats = self._db.formats(book.id, verify_formats=True)
			if len(formats) > 0:
				book.filepath = self._db.format_abspath(book.id, formats[0])
			else:
				book.filepath = None

			books.append(book)
	
		return books

class PyroTechnyLibrary:
	SYNC_STATE_FILE = ".calibre_to_hugo.sync_state.json"

	_calibre_library : CalibreLibrary
	_path: str
	_tempdir: str
	_state_file: str
	_state: dict

	def __init__(self, path: str, calibre_library: CalibreLibrary):
		self._books = []
		self._calibre_library = calibre_library
		self._path = path
		self._state = {}
		self._state["books"] = []

		# Create path directories
		if not os.path.exists(self._path):
			os.makedirs(self._path, 0o755)

		self._state_filepath = os.path.join(self._path, self.SYNC_STATE_FILE)
		self._state_load()

	def __del__(self):
		self._state_save()

	def _state_load(self):
		if not os.path.exists(self._state_filepath):
			return

		with open(self._state_filepath, "r") as fd:
			self._state = json.load(fd)

	def _state_save(self):
		return # TODO
		with open(self._state_filepath, "w") as fd:
			json.dump(self._state, fd, indent=2)

	def _generate_book_page(self, path, book):
		filepath = os.path.join(path, f'{book.filehash}.md')
		if os.path.exists(filepath):
			os.remove(filepath)

		print(f"GEN {filepath}")

		with open(filepath, "w") as fd:
			data = f'''---
title: "{book.title}"
description: ""
featured_image: "/images/site/library-header.jpg"
type: page
---

'''
			fd.write(data)

			cover = os.path.basename(book.cover)

			fd.write(f'![{cover}]({config.LIBRARY_BASE_URL}/{cover})\n')
			fd.write(f'* Authors: {book.authors}\n')
			fd.write(f'* [Download]({config.LIBRARY_BASE_URL}/{book.filename})\n\n')
			fd.write(f'[Back]({config.LIBRARY_BASE_URL}/\n)')
	
	def synchronize(self):
		# Load books from calibre
		books = self._calibre_library.books()
		for book in books:
			book.ebook_filename()
			book.cover_save(config.HUGO_STATIC_CONTENT_LIBRARY_PATH)  
			book.ebook_save(config.HUGO_STATIC_CONTENT_LIBRARY_PATH)
			self._state["books"].append(book)

	""" Generate hugo markdown content files """
	def generate(self):
		# index ...
		data = """---
title: Library
description: 'PyroTechny.EU'
featured_image: '/images/site/library-header.jpg'
type: page
menu: main
---

"""
		print(f"GEN {config.HUGO_CONTENT_LIBRARY_INDEX_FILEPATH}")
		with open(config.HUGO_CONTENT_LIBRARY_INDEX_FILEPATH, "w") as fd:
			fd.write(data)
			for book in self._state["books"]:
				fd.write(f"- [{book.title}]({config.LIBRARY_BASE_URL}/{book.filehash}/)\n")	

		# per-book page generation
		book_page_path = config.HUGO_CONTENT_LIBRARY_PATH
		if not os.path.exists(book_page_path):
			os.makedirs(book_page_path, 0o755)

		# TODO synced state instead of calibre copy....
		for book in self._state["books"]:
			self._generate_book_page(book_page_path, book)

def main():
	calibre_library = CalibreLibrary(config.CALIBRE_LIBRARY_PATH)
	pyrotechny_library = PyroTechnyLibrary(config.HUGO_STATIC_CONTENT_LIBRARY_PATH, calibre_library)
	pyrotechny_library.synchronize()
	pyrotechny_library.generate()

if __name__ == "__main__":
    main()
