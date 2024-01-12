#!/bin/sh
DISK_PATH="/Users/jerry/Downloads/library.pyrotechny.eu/books"
GDRIVE_PATH="gdrive:library.pyrotechny.eu/ebooks"
RCLONE_ARGS="--progress --config rclone.conf"
#rclone --config rclone.conf ls gdrive:library.pyrotechny.eu/ebooks
/usr/local/bin/rclone ${RCLONE_ARGS} sync ${DISK_PATH} ${GDRIVE_PATH}
