STREAMLIT_PATH := $(shell which streamlit)

all:
	${STREAMLIT_PATH} run streamlit_app.py

local_portfolios:
	./comp_pel_a_av.py
