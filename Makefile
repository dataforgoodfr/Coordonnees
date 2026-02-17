build:
	cd coordo-ts && npm run build
	cp -r coordo-ts/dist/* coordo-py/coordo/static/
