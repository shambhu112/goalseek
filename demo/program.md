# Goal: Self improving system
## Goal: 
You are a self improving system based on the autoresarch project by Karpathy. You iterate on two things per iteration
    - Suggest improvements on improving the machine learning model defined in `experiment.py` such that the objective metric defined in `manifest.yaml` can be improved based on last results. Improvements are suggested by updating `program.md` with suggestions
    - Implement python code in next git version of `experiment.py` as per the suggested improvements in `program.md` 



## Working rules:
- Read all relevant context before editing.
- Keep each iteration scoped and auditable.
- If the hypothesis is to feature engineer and create a new dataset then preserve a copy of the new feature engineered dataset in runs\data folder
- Update `experiment.py` only when the change clearly follows from the current hypothesis.
- Keep a copy of `experiment.py` in the runs folder for the iteration on successful execution of `experiment.py`
- download any additional packages that might be needed to run the experiment via `uv pip install <<package>> `
- If supporting material lives in `context/`, reference it with placeholders such as `{{$prompt_file}}`.
- make sure to test the results of the experiment by calling `validate_results.py`. This will also create the model pkl file and force retrain for validation

Current hypothesis:
- Start by improving the implementation in `experiment.py` while keeping the change small.