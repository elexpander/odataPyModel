.PHONY: docs release clean build

clean:
	rm -rf env output/* tmp/*

build:
	virtualenv env && source env/bin/activate && \
	pip install -r requirements.txt

test: clean build
	source env/bin/activate && \
	python app.py
