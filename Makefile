F=*.py
NOSEARGS=--nocapture --nologcapture

venv-sync: .venv
	.venv/bin/pip install -r requirements.txt

tests: .venv

coverage: .venv

.venv:
	sudo apt-get install build-essential python-dev libmysqlclient-dev python-mysqldb
	virtualenv .venv
	$(MAKE) venv-sync

must_be_root:
	@test $$(id -u) = 0

populate: must_be_root
	echo I_AM_A_POPULAR_ROOT

lint:
	pylint $(F)
	pep8 --ignore=E501 $(F)
