build:
	cd coordo-ts && npm run build
	mkdir -p coordo-py/coordo/static/
	cp -r coordo-ts/dist/* coordo-py/coordo/static/
