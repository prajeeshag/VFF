#!/bin/bash
dir="$(dirname "$0")"
cd "$dir" || exit 1
mkdir -p archive
echo "archiving" > .archive_lock
sleep 10
(python ./manage.py archive && echo "done" > .archive_lock) || echo "Error" > .archive_lock
echo "Done" > .archive_lock
