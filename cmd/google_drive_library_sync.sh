#!/bin/sh
DISK_PATH="/Users/jerry/files/pyrotechnics/cache/pyrotechny.eu/library/ebooks"
GDRIVE_PATH="gdrive:library.pyrotechny.eu/ebooks"
RCLONE_ARGS="--progress --config rclone.conf"
#rclone --config rclone.conf ls ${GDRIVE_PATH}
/usr/local/bin/rclone ${RCLONE_ARGS} sync ${DISK_PATH} ${GDRIVE_PATH}
