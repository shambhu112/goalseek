# Bash Steps for 3 Full Iterations

This file shows the exact bash commands to run a `fast_research` project through baseline plus 3 full iterations.

## Option 1: Fresh project from scratch

Create the virtual environment and install the package:

### Step 1
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```
### Step 2
Create a new project:
> **Note** : Dependency here for claude code CLI
```bash
uv run goalseek project init demo --provider claude_code --model claude-haiku-4-5-20251001
```
### Step 3
```bash
./move-testpackage.sh --overwrite ./demo
```
### Step 4
Validate the manifest and inspect setup:
- Make sure that the metric in manfest is accurate. For the kaggle irrigation dataset update the metric to be `balanced accuracy score`
- Update `demo/manifest.yaml` with informtion below

```
metric:
  name: Balanced accuracy Score
  direction: maximize

```
```bash
uv run goalseek manifest validate ./demo
```

### Step 5
Adjust timeouts in
`demo/config/project.yaml`

### Step 5
Run the one time setup that creates the train and test datasets based on Kaggle's dataset

```bash
uv run goalseek setup ./demo
```
> **Note** : if the CLI complains for python packages please install them


### Step 6
check if repo is clean from a git commit standpoint. This is needed as every iteration run by goalseek creates a git commit

```{bash}
uv run goalseek gittreeclean --message  "clean repo" ./demo
```
### Step 7

Run the baseline. This step creates the first version of the run. it will run the base model you have provided in `experiment.py` and verify results with `verify_results.py`

```bash
uv run goalseek baseline ./demo
```
### Step 8
Run 3 full iterations in autonomus mode.
```bash
uv run goalseek run ./demo --iterations 3
```

Check the final state and summary:

```bash
uv run goalseek status ./demo
uv run goalseek summary ./demo
```

## Potential Failures and fixes

1. `working tree must be clean before applying a change` 

Check what is dirty:

```bash
git -C demo status --short
```

If you want to keep the change, commit it:

```bash
git -C demo add --all
git -C demo commit -m "save local changes"
```

If you do not want to keep the change, restore the edited file or files:

```bash
git -C demo restore <path>
```

Then rerun:

```bash
uv run goalseek run ./demo --iterations 3
```

## Useful inspection commands during the 3-iteration run

Show loop state:

```bash
cat ./demo/logs/state.json
```

Show the latest recorded results:

```bash
tail -n 10 ./demo/logs/results.jsonl
```

Inspect a specific iteration directory:

```bash
ls ./demo/runs/0001
ls ./demo/runs/0002
ls ./demo/runs/0003
```

Open the main artifacts for one iteration:

```bash
cat ./demo/runs/0001/prompt.md
cat ./demo/runs/0001/provider_output.md
cat ./demo/runs/0001/result.json
```
