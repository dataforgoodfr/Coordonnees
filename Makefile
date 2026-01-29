build-js:
	cd js && npm run build
	cd demo && uv run manage.py collectstatic
