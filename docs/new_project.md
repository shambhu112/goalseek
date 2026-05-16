# Context
This document explain the process of setting a new goalseek project

# References
- Creating Baselines and Iterations - https://shambhu112.github.io/goalseek/docs/guides/baseline-and-iterations
- Loop Engine Phases  https://shambhu112.github.io/goalseek/docs/architecture/loop-engine-phases

# Steps
1. Create a new project scaffold.
The project scaffold is created using the command 
```
uv run goalseek project init red_team_first --provider codex --model gpt-5.4-mini
```
Note: the user will provide the project name like `red_team_first` and the model like `gpt-5.4-mini` . 

2. Edit and Validate the manifest file `manifest.yaml`
For Manifest File, make sure about the following
```
  - path: manifest.yaml
    mode: read_only
  - path: program.md
    mode: read_only
  - path: setup.py
    mode: read_only
  - path: validate_results.py
    mode: hidden
  - path: hidden/**
    mode: hidden
  - path: config/**
    mode: read_only
  - path: runs/**
    mode: generated
  - path: logs/**
    mode: generated
  
```
Note: Other entries in the manifest will project dependent.

Validate the manifest with the command 
```
uv run goalseek manifest validate ./red_team_first
```

3. Make sure that you look at `./red_team_first/config/project.yaml` to check for 
  - Correct LLM Provider is set for Hypothesis and Implementation
  - Logging as per what you need

4. The Basic Project Structure is ready. Now focus on `'baseline_creation.md`

