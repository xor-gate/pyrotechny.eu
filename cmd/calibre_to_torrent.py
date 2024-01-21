#!/Applications/calibre.app/Contents/MacOS/calibre-debug calibre_to_torrent.py
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
		title = self.title
		ext = pathlib.Path(self.filepath).suffix
		self.filename = f"{title}{ext}"
		self.filename = self.filename.replace(",", ".")
		self.filename = self.filename.replace(";", "")
		self.filename = self.filename.replace(":", ".")
		self.filename = self.filename.replace("/", "-")
		self.filename = self.filename.replace("'", "")
		self.filename = self.filename.replace(" ", ".")
		self.filename = self.filename.replace("..", ".")
		return self.filename
		
	""" Save the ebook from the calibre library to the path """
	def ebook_save(self, path: str) -> str:
		filepath = os.path.join(path, self.ebook_filename())

		if os.path.exists(filepath):
			return

		print(f"COPY {self.filepath} -> {filepath}")
		shutil.copyfile(self.filepath, filepath)
		return filepath


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

class PyroTechnyEbookLibraryTorrent:
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

		# Create cache pat
		if not os.path.exists(self._path):
			print(f"CREATE {self._path}")
			os.makedirs(self._path, 0o755)

	def synchronize(self):
		# Load books from calibre
		books = self._calibre_library.books()
		for book in books:
			#print(f"{book.to_json()}")
			book.ebook_save(self._path)

def main():
	calibre_library = CalibreLibrary(config.CALIBRE_LIBRARY_PATH)
	pyrotechny_library = PyroTechnyEbookLibraryTorrent(config.EBOOK_LIBRARY_TORRENT_CACHE_DIR, calibre_library)
	pyrotechny_library.synchronize()

if __name__ == "__main__":
    main()

