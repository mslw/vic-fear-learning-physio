# vic-fear-learning-physio
Code for replicating analysis from our vicarious fear learning study.
[Preprint on biorXiv](https://www.biorxiv.org/content/10.1101/2020.01.29.924720v1).

## Pipeline
* `cp emocon_config.ini.example emocon_config.ini` and edit paths
* run `load_data.py` to extract from acq into numpy arrays (time consuming due to marker detection!)
* run `emg_master.py` and `eda_master.py` for trial scoring
* run `collect_scores.py` to create long tables with trial scores
* run `wrangle_table` to create tables with summary scores for statistical analysis
* use `Publication_Plots.ipynb` notebook to produce plots

## Acknowledgements
Repository includes a copy of cvxEDA.py, taken from https://github.com/lciti/cvxEDA (GPL-3.0).

## Requirements
The analysis can be reproduced using libraries listed in the requirements file, using python 3.7.5.

## Notes
To use ipython with a virtual environment, add a kernel. Full instructions [here](https://anbasile.github.io/programming/2017/06/25/jupyter-venv/).
In short:
```
(venv) $ pip install ipykernel
(venv) $ ipython kernel install --user --name=projectname
```
