#!/bin/bash
# A Shell Script To Remove output data from Jupyter Notebooks
# This should be manually run before doing any git commits
#
# I had attempted to automate this process using filters and git configs
# described here: 
# https://zhauniarovich.com/post/2020/2020-10-clearing-jupyter-output-p3/
#
# This ran the clean, but any notebooks pushed to the remote were zero bytes
# For now resorting to the manual method

echo "Removing output from all notebooks cells..."
jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace *.ipynb
