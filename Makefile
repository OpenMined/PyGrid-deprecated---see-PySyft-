# Global environment variables.
REQ_DIR=pip-dep
PYTHON_MODULE_PATH=grid

venv: venv/bin/activate

reqs: $(REQ_DIR)/requirements.txt $(REQ_DIR)/requirements_dev.txt

venv/bin/activate: reqs
	test -e venv/bin/activate || python3 -m venv venv
	. venv/bin/activate; pip install -Ur $(REQ_DIR)/requirements.txt; pip install -Ur $(REQ_DIR)/requirements_dev.txt; python setup.py install
	touch venv/bin/activate


install_hooks: venv
	venv/bin/pre-commit install

notebook: venv
	(. venv/bin/activate; \
		python setup.py install; \
		python -m ipykernel install --user --name=grid; \
		jupyter notebook;\
	)

lab: venv
	(. venv/bin/activate; \
		python setup.py install; \
		python -m ipykernel install --user --name=grid; \
		jupyter lab;\
	)

.PHONY: test
test: venv
	(. venv/bin/activate; \
		python setup.py install; \
		venv/bin/coverage run -m pytest test;\
	)

format:
	yapf --verbose --in-place --recursive ${PYTHON_MODULE_PATH} --style='{based_on_style: pep8, indent_width:4, column_limit:80}'
	isort --verbose ${PYTHON_MODULE_PATH}
	docformatter --in-place --recursive ${PYTHON_MODULE_PATH}

clean:
	rm -rf venv
