#!/bin/sh
case $1 in
	loader)
		echo "loading"
		PJ="/etc/uo/params.json"
		if [ ! -z $2 ]; then
			PJ=$2
		fi
		python3 loader.py $PJ
		;;
	server)
		echo "serving"
		# gunicorn --bind '[::]:8000' wsgi
		python server.py
		;;
	*)
		echo "wat?"
esac
