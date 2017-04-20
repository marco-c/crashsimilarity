init:
	pip install -r requirements.txt
	pip install -r test-requirements.txt

test:
	py.test tests
