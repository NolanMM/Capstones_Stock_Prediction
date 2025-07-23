import os
import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

NOTEBOOK_PATH = os.path.join(os.path.dirname(__file__), "Walk-Forward.ipynb")

def test_walk_forward_notebook_runs(tmp_path):
    """
    Load and execute the entire Walk-Forward notebook.  
    If any cell raises an exception, this test will fail.
    """
    # Read the .ipynb
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Execute
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    # Set working directory so relative imports/data paths resolve
    ep.preprocess(nb, {"metadata": {"path": os.path.dirname(NOTEBOOK_PATH)}})
