FROM docker.moscow.alfaintra.net/modelwrapper:1.4
RUN rm -rf /models_handler/models/*
COPY models/* /models_handler/models/
COPY __init__.py /models_handler/
COPY core.py /models_handler/
COPY models/test_start.py /