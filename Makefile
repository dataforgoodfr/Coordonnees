build:
	cd coordo-ts && npm install && npm run build
	mkdir coordo-py/coordo/static/
	cp -r coordo-ts/dist/* coordo-py/coordo/static/
