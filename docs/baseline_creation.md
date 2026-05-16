# Context
This document explains the process of creating the first version of three important files for Goalseek. These are `experiment.py` , `program.md` , 'validate_results.py`. 
Once these are ready you can run for create a baseline for your project and that can be run as iteration 0.

# Reference :
1. Baseline Creation and Iterations : https://shambhu112.github.io/goalseek/docs/guides/baseline-and-iterations
2. Loop Engine Phases : docs/loop_engine_phases.md


# experiment.py
- This is the python file responsible run at the stage of APPLY_CHANGE in Loop engine Phases
- the `experiment.py` can be modified by Agentic Coding Engine like Codex / Claude code depending on the experiment need
- The goal is to implement the first version of `experiment.py` that can be used for creating the baseline

# program.md
- used in **READ_CONTEXT**, **PLAN**, **APPLY_CHANGE** phases of Loop engine by the Agentic coding provider. 
- It gets used in each iteration and hence write if such that it can be reused again and again and again. 
- It directs the Agentic Coding Provider to create plan and implementation for the iteration



