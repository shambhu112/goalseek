# Codex Provider Test Cases

| Test case | Condition | What it tests |
| --- | --- | --- |
| `test_codex_capabilities_prefers_configured_executable` | Provider config has explicit executable. | Uses configured executable and reports available capabilities. |
| `test_codex_capabilities_uses_path_lookup` | SDK disabled; `codex` found on `PATH`. | Falls back to CLI path lookup. |
| `test_codex_capabilities_reports_unavailable_when_executable_missing` | SDK disabled; no CLI executable found. | Reports provider unavailable. |
| `test_codex_plan_invokes_run_command` | Plan request with mocked CLI success. | Builds expected CLI command and maps success response. |
| `test_codex_implement_invokes_run_command` | Implementation request with mocked CLI success. | Uses same CLI path for implementation mode. |
| `test_run_cli_returns_error_when_executable_missing` | CLI capabilities have no executable. | Returns exit code 1 with `executable not found`. |
| `test_run_cli_returns_stderr_on_failure` | CLI exits nonzero with stderr. | Uses stderr as raw text and error. |
| `test_run_cli_prefers_stdout_on_success` | CLI exits zero with stdout and stderr. | Prefers stdout and clears error. |
| `test_codex_cli_omits_model_when_config_uses_default` | Request model is `default`. | Omits `--model` flag from CLI command. |
| `test_codex_plan_passes_requested_model_to_cli` | Plan request has custom model. | Passes requested model to CLI. |
| `test_codex_implement_passes_requested_model_to_cli` | Implementation request has custom model. | Passes requested model to CLI. |
| `test_codex_plan_rejects_dangerous_bypass_flag` | Plan request through mocked CLI. | Verifies bypass sandbox flag is present. |
| `test_codex_implement_rejects_dangerous_bypass_flag` | Implementation request through mocked CLI. | Verifies bypass sandbox flag is present. |
| `test_codex_plan_passes_non_interactive_exec_command` | Plan request through mocked CLI. | Builds exact noninteractive `codex exec` command. |
| `test_codex_uses_default_model_without_explicit_model_flag` | Model is `default`. | Runs without explicit model flag. |
| `test_codex_propagates_empty_stdout_and_stderr_failure_message` | CLI fails with no output. | Creates fallback failure message. |
| `test_codex_forced_sdk_runs_thread` | SDK transport forced with fake SDK. | Starts SDK thread, passes model/cwd/effort, captures metadata. |
| `test_codex_sdk_reuses_thread_across_plan_and_implementation` | SDK reuse enabled with fake SDK. | Reuses stored thread between plan and implementation. |
| `test_codex_sdk_resume_failure_starts_new_thread` | Stored SDK thread is stale. | Drops stale thread and starts a new one. |
| `test_codex_sdk_treats_turn_error_as_provider_failure` | SDK turn returns an error. | Maps turn error to provider failure. |
| `test_codex_sdk_empty_final_response_is_successful_empty_output` | SDK succeeds with no final response. | Treats empty final response as successful empty output. |
| `test_codex_sdk_timeout_maps_to_124` | SDK run raises `TimeoutError`. | Maps timeout to exit code 124. |
| `test_codex_cli_fallback_reports_missing_executable_when_no_sdk_or_cli` | Auto transport; SDK and CLI missing. | Falls back to CLI and reports missing executable. |
| `test_codex_cli_extreme_prompt_preserves_newlines_and_unicode` | Large prompt with newlines and unicode. | Preserves prompt content and appends plugin runtime options. |
| `test_codex_auto_falls_back_to_cli_when_sdk_missing` | Auto transport; SDK missing; CLI available. | Falls back to CLI and records fallback metadata. |
| `test_codex_forced_sdk_errors_when_sdk_missing` | SDK transport forced; SDK missing. | Returns SDK unavailable error. |
| `test_codex_cli_prompt_includes_runtime_options` | CLI request has parallel, research, plugin, and MCP config. | Injects runtime options into prompt. |
| `test_live_codex_sdk_smoke` | Live enabled with API key and `openai_codex`. | Real SDK can login, start thread, and return expected text. |
| `test_live_codex_provider_sdk_plan_smoke` | Live enabled with API key and `openai_codex`. | Real provider SDK plan path succeeds. |
| `test_live_codex_provider_sdk_reuses_thread` | Live enabled with API key and `openai_codex`; reuse enabled. | Real provider SDK reuses thread and preserves context. |
| `test_live_codex_provider_sdk_fails_with_missing_executable` | Live enabled; SDK transport points at a nonexistent executable. | Provider returns failure metadata instead of running or crashing. |
| `test_live_codex_provider_sdk_fails_with_invalid_model` | Live enabled; SDK transport uses an invalid model name. | Provider maps live Codex model/API rejection to a nonzero response. |
| `test_live_codex_provider_sdk_fails_with_broken_executable` | Live enabled; SDK transport points at an executable that exits immediately. | Provider reports app-server startup failure with empty raw output. |

Live tests skip unless `GOALSEEK_LIVE_CODEX=1`, `OPENAI_API_KEY` is set, and `openai_codex` imports. Some local SDK installs also need a Codex app-server runtime or an explicit `AppServerConfig(codex_bin=...)` path.
