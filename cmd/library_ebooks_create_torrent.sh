#!/bin/sh
# Needs py3createtorrent
##
OUTPUT_DIR="$HOME/files/pyrotechnics/cache"
EBOOK_LIBRARY_DIRECTORY="${OUTPUT_DIR}/fireworks_and_pyrotechnics_ebook_library_by_pyrotechny_eu"
NAME="fireworks_and_pyrotechnics_ebook_library_by_pyrotechny_eu" 
COMMENT="Pyrotechnics and fireworks ebook library by PyroTechny.EU"

py3createtorrent --exclude-pattern '.DS_Store' -o "${OUTPUT_DIR}" -n "${NAME}" -c "${COMMENT}" -t best20 ${EBOOK_LIBRARY_DIRECTORY}
