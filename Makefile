node_modules:
    npm install

build-js: node_modules
    cd js && npm run build
	cd demo && uv run manage.py collectstatic
