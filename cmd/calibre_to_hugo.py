#!/Applications/calibre.app/Contents/MacOS/calibre-debug calibre_to_hugo.py
# See: https://manual.calibre-ebook.com/db_api.html
import os
import json
import copy
import shutil
import pathlib
import hashlib
import urllib
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

	@staticmethod
	def _get_filesize_str(path: str) -> str:
		size = os.path.getsize(path)
		if size < 1024:
			return f"{size} bytes"
		elif size < pow(1024,2):
			return f"{round(size/1024, 2)} KB"
		elif size < pow(1024,3):
			return f"{round(size/(pow(1024,2)), 2)} MB"
		elif size < pow(1024,4):
			return f"{round(size/(pow(1024,3)), 2)} GB"

	def books(self) -> 'list[CalibreLibraryBook]':
		books = []
		book_ids = self._db.all_book_ids()

		for book_id in book_ids:
			# TODO check loaded state with state of calibre based on book.id
			#      hashing takes way to long...
			book = CalibreLibraryBook(self._db)
			book.id = book_id
			book.title = self._db.field_for("title", book.id)
			book.authors = self._db.field_for("authors", book.id)
			book.comments = self._db.field_for("comments", book.id) 
			book._metadata = self._db.get_metadata(book.id)
			book.ids = book._metadata.get_identifiers()

			# Select only first ebook format 
			formats = self._db.formats(book.id, verify_formats=True)
			if len(formats) > 0:
				book.filepath = self._db.format_abspath(book.id, formats[0])
				book.filesize = self._get_filesize_str(book.filepath)
			else:
				book.filepath = None
				book.filesize = 0

			books.append(book)
	
		return books

class PyroTechnyLibrary:
	_calibre_library : CalibreLibrary
	_path: str
	_tempdir: str
	_google_drive_file_db: list

	def __init__(self, path: str, calibre_library: CalibreLibrary):
		self._books = []
		self._calibre_library = calibre_library
		self._path = path
		self._state = {}
		self._state["books"] = []

		# Create path directories
		if not os.path.exists(self._path):
			print(f"CREATE {self._path}")
			os.makedirs(self._path, 0o755)

		self._load_google_drive_file_db()

	def _get_google_drive_value_from_filename(self, filename: str, key: str) -> str:
		value = ""
		for file in self._google_drive_file_db:
			if filename == file["filename"]:
				value = file[key]
				break
		return value

	def _load_google_drive_file_db(self):
		resp = urllib.request.urlopen(config.GOOGLE_DRIVE_EBOOK_LIBRRARY_DB_JSON_URL)
		self._google_drive_file_db = json.loads(resp.read())
		print(self._google_drive_file_db)

	def _generate_book_dl_page(self, path, book):
		pass

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
			cover_url = self._get_google_drive_value_from_filename(cover, "view_url")

			book_url = self._get_google_drive_value_from_filename(book.filename, "view_url")
			book_dl_url = self._get_google_drive_value_from_filename(book.filename, "download_url")

			authors = list(book.authors)
			authors = ', '.join(authors)
			if len(book.authors) == 1:
				if book.authors[0] == "Unknown":
					authors = None

			fd.write(f'<a href="{book_url}" target="_blank">![{cover}]({cover_url})</a>\n')

			if authors:
				author_suffix = ''
				if len(book.authors) > 1:
					author_suffix = 's'
				fd.write(f"* Author{author_suffix}: {authors}\n")

			if book.ids:
				fd.write(f'* IDs:\n')
				for key, value in book.ids.items():
					print(key)
					if key == "amazon":
						fd.write(f'  * Amazon: <a href="https://www.amazon.com/dp/{value}" target="_blank">{value}</a>\n')
					elif key == "google":
						fd.write(f'  * Google: <a href="https://books.google.com/books?id={value}" target="_blank">{value}</a>\n')
					elif key == "isbn":
						fd.write(f'  * ISBN: <a href="https://www.worldcat.org/isbn/{value}" target="_blank">{value}</a>\n')
						
				
			fd.write(f'* <a href="{book_url}" target="_blank">View</a>\n\n')
			fd.write(f'* [Download]({book_dl_url}) ({book.filesize})\n\n')

			if book.comments:
				fd.write(f'## Description')
				fd.write(f'{book.comments}\n\n')

			fd.write(f'[Back]({config.LIBRARY_EBOOKS_BASE_URL}/)\n')
	
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
				fd.write(f"- [{book.title}]({config.LIBRARY_EBOOKS_BASE_URL}/{book.filehash}/)\n")	

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
