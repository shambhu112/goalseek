# Graph Report - .  (2026-05-07)

## Corpus Check
- 167 files · ~142,436 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 747 nodes · 1499 edges · 95 communities detected
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 683 edges (avg confidence: 0.76)
- Token cost: 21,580 input · 5,720 output

## Community Hubs (Navigation)
- [[_COMMUNITY_CLI Command Layer|CLI Command Layer]]
- [[_COMMUNITY_Core Loop Engine|Core Loop Engine]]
- [[_COMMUNITY_Provider Specs & Architecture|Provider Specs & Architecture]]
- [[_COMMUNITY_Git Ops & Configuration|Git Ops & Configuration]]
- [[_COMMUNITY_Claude Code Provider|Claude Code Provider]]
- [[_COMMUNITY_Config & Data Models|Config & Data Models]]
- [[_COMMUNITY_Provider Protocol & Direction|Provider Protocol & Direction]]
- [[_COMMUNITY_Validation & Error Handling|Validation & Error Handling]]
- [[_COMMUNITY_CLI Rich Rendering|CLI Rich Rendering]]
- [[_COMMUNITY_GoalSeek Algorithm Diagram|GoalSeek Algorithm Diagram]]
- [[_COMMUNITY_Sidebar Navigation UI|Sidebar Navigation UI]]
- [[_COMMUNITY_Toast Notification System|Toast Notification System]]
- [[_COMMUNITY_App Icon SVG|App Icon SVG]]
- [[_COMMUNITY_Alert Dialog Component|Alert Dialog Component]]
- [[_COMMUNITY_Breadcrumb Navigation|Breadcrumb Navigation]]
- [[_COMMUNITY_Context Menu Component|Context Menu Component]]
- [[_COMMUNITY_Pagination Component|Pagination Component]]
- [[_COMMUNITY_Select Dropdown|Select Dropdown]]
- [[_COMMUNITY_Kaggle ML Experiment|Kaggle ML Experiment]]
- [[_COMMUNITY_Sheet Component|Sheet Component]]
- [[_COMMUNITY_Run List View|Run List View]]
- [[_COMMUNITY_Carousel Component|Carousel Component]]
- [[_COMMUNITY_Drawer Component|Drawer Component]]
- [[_COMMUNITY_Dropdown Menu|Dropdown Menu]]
- [[_COMMUNITY_Form Component|Form Component]]
- [[_COMMUNITY_Folder Picker Dialog|Folder Picker Dialog]]
- [[_COMMUNITY_Metric Chart View|Metric Chart View]]
- [[_COMMUNITY_Run Detail Panel|Run Detail Panel]]
- [[_COMMUNITY_Card Component|Card Component]]
- [[_COMMUNITY_OTP Input Component|OTP Input Component]]
- [[_COMMUNITY_Item Component|Item Component]]
- [[_COMMUNITY_Menubar Component|Menubar Component]]
- [[_COMMUNITY_Navigation Menu|Navigation Menu]]
- [[_COMMUNITY_Toggle Group|Toggle Group]]
- [[_COMMUNITY_Tooltip Component|Tooltip Component]]
- [[_COMMUNITY_Apple Touch Icon Assets|Apple Touch Icon Assets]]
- [[_COMMUNITY_Dark Theme Icon|Dark Theme Icon]]
- [[_COMMUNITY_Light Theme Icon|Light Theme Icon]]
- [[_COMMUNITY_Diff Viewer Component|Diff Viewer Component]]
- [[_COMMUNITY_Project Header View|Project Header View]]
- [[_COMMUNITY_Alert Component|Alert Component]]
- [[_COMMUNITY_Avatar Component|Avatar Component]]
- [[_COMMUNITY_Chart Utilities|Chart Utilities]]
- [[_COMMUNITY_Collapsible Component|Collapsible Component]]
- [[_COMMUNITY_Radio Group|Radio Group]]
- [[_COMMUNITY_Scroll Area|Scroll Area]]
- [[_COMMUNITY_Slider Component|Slider Component]]
- [[_COMMUNITY_Tabs Component|Tabs Component]]
- [[_COMMUNITY_Mobile Detection Hook|Mobile Detection Hook]]
- [[_COMMUNITY_CLI Entry Point|CLI Entry Point]]
- [[_COMMUNITY_Test Package Setup|Test Package Setup]]
- [[_COMMUNITY_Test Package Init|Test Package Init]]
- [[_COMMUNITY_Next.js Root Layout|Next.js Root Layout]]
- [[_COMMUNITY_Web Home Page|Web Home Page]]
- [[_COMMUNITY_Runs API Route|Runs API Route]]
- [[_COMMUNITY_Theme Provider|Theme Provider]]
- [[_COMMUNITY_Demo Explorer|Demo Explorer]]
- [[_COMMUNITY_Accordion Component|Accordion Component]]
- [[_COMMUNITY_Badge Component|Badge Component]]
- [[_COMMUNITY_Button Group|Button Group]]
- [[_COMMUNITY_Button Component|Button Component]]
- [[_COMMUNITY_Calendar Component|Calendar Component]]
- [[_COMMUNITY_Checkbox Component|Checkbox Component]]
- [[_COMMUNITY_Command Component|Command Component]]
- [[_COMMUNITY_Dialog Component|Dialog Component]]
- [[_COMMUNITY_Empty State|Empty State]]
- [[_COMMUNITY_Field Component|Field Component]]
- [[_COMMUNITY_Hover Card|Hover Card]]
- [[_COMMUNITY_Input Group|Input Group]]
- [[_COMMUNITY_Keyboard Shortcut Display|Keyboard Shortcut Display]]
- [[_COMMUNITY_Label Component|Label Component]]
- [[_COMMUNITY_Separator Component|Separator Component]]
- [[_COMMUNITY_Skeleton Loader|Skeleton Loader]]
- [[_COMMUNITY_Sonner Toast|Sonner Toast]]
- [[_COMMUNITY_Switch Component|Switch Component]]
- [[_COMMUNITY_Textarea Component|Textarea Component]]
- [[_COMMUNITY_Docs Site Config|Docs Site Config]]
- [[_COMMUNITY_Docs Sidebars|Docs Sidebars]]
- [[_COMMUNITY_Docs Index Page|Docs Index Page]]
- [[_COMMUNITY_Next.js Type Defs|Next.js Type Defs]]
- [[_COMMUNITY_Artifact Viewer|Artifact Viewer]]
- [[_COMMUNITY_Aspect Ratio|Aspect Ratio]]
- [[_COMMUNITY_Input Component|Input Component]]
- [[_COMMUNITY_Popover Component|Popover Component]]
- [[_COMMUNITY_Progress Component|Progress Component]]
- [[_COMMUNITY_Resizable Layout|Resizable Layout]]
- [[_COMMUNITY_Spinner Component|Spinner Component]]
- [[_COMMUNITY_Toast Component|Toast Component]]
- [[_COMMUNITY_Toaster Component|Toaster Component]]
- [[_COMMUNITY_Toggle Component|Toggle Component]]
- [[_COMMUNITY_Placeholder Logo Triangle|Placeholder Logo Triangle]]
- [[_COMMUNITY_Placeholder Logo Acme|Placeholder Logo Acme]]
- [[_COMMUNITY_Placeholder User Avatar|Placeholder User Avatar]]
- [[_COMMUNITY_Placeholder Image|Placeholder Image]]
- [[_COMMUNITY_Placeholder Image 2|Placeholder Image 2]]

## God Nodes (most connected - your core abstractions)
1. `LoopEngine` - 40 edges
2. `Repo` - 37 edges
3. `ClaudeCodeProvider` - 32 edges
4. `project_factory()` - 30 edges
5. `GET()` - 27 edges
6. `ProjectService` - 25 edges
7. `_request()` - 23 edges
8. `invoke()` - 22 edges
9. `info()` - 20 edges
10. `ProviderSelection` - 20 edges

## Surprising Connections (you probably didn't know these)
- `validate_results.py (verification script)` --semantically_similar_to--> `VerificationRunner`  [INFERRED] [semantically similar]
  test-package/program.md → project-wiki.md
- `Execute 5+ consecutive steps and verify phase progression.` --uses--> `ProjectStateError`  [INFERRED]
  tests\unit\test_step_engine.py → src\goalseek\errors.py
- `Run the same step twice and verify result consistency.` --uses--> `ProjectStateError`  [INFERRED]
  tests\unit\test_step_engine.py → src\goalseek\errors.py
- `Test that phases follow expected order.` --uses--> `ProjectStateError`  [INFERRED]
  tests\unit\test_step_engine.py → src\goalseek\errors.py
- `Pass None as project root; expect TypeError or AttributeError.` --uses--> `ProjectStateError`  [INFERRED]
  tests\unit\test_step_engine.py → src\goalseek\errors.py

## Hyperedges (group relationships)
- **Seven-Phase Research Loop (READ_CONTEXTâ†’PLANâ†’APPLYâ†’COMMITâ†’VERIFYâ†’DECIDEâ†’LOG)** — wiki_loop_engine, wiki_step_engine, loop_phases_read_context, loop_phases_plan, loop_phases_apply_change, loop_phases_commit, loop_phases_verify, loop_phases_decide, loop_phases_log [EXTRACTED 1.00]
- **Provider Ecosystem (Claude/Gemini/Codex/Opencode/Fake implement ProviderAdapter)** — wiki_provider_adapter, wiki_claude_code_provider, wiki_gemini_provider, wiki_fake_provider, agentspec_codex_provider, agentspec_opencode_provider [EXTRACTED 1.00]
- **Kaggle Irrigation Prediction Test Scenario (dataset + experiment + validation)** — overview_kaggle_s6e4, data_dict_irrigation_dataset, testpkg_experiment_py, testpkg_validate_results, overview_balanced_accuracy [EXTRACTED 0.95]
- **Icon Visual Composition** —  [INFERRED 1.00]

## Communities

### Community 0 - "CLI Command Layer"
Cohesion: 0.06
Nodes (61): init_project(), run_setup(), run_step(), baseline_command(), invoke(), project_factory(), direct_command(), write_fake_provider() (+53 more)

### Community 1 - "Core Loop Engine"
Cohesion: 0.06
Nodes (28): add_direction(), get_status(), run_baseline(), run_loop(), ArtifactStore, _extract_heading(), ProviderRequest, info() (+20 more)

### Community 2 - "Provider Specs & Architecture"
Cohesion: 0.05
Nodes (64): CodexProvider, Error Hierarchy (ManifestValidationError, GitOperationError, etc.), goalseek Agent-Ready Implementation Specification, Implementation Order (Phases 1-6), Non-Negotiable Product Invariants, OpencodeProvider, Project Scaffold Layout, ProviderAdapter Protocol (plan/implement/capabilities) (+56 more)

### Community 3 - "Git Ops & Configuration"
Cohesion: 0.07
Nodes (27): clean_git_tree(), EffectiveConfig, ContextReader, ConfigError, GitOperationError, ProjectStateError, sha256_file(), ContextBundle (+19 more)

### Community 4 - "Claude Code Provider"
Cohesion: 0.1
Nodes (35): ProviderCapabilities, ClaudeCodeProvider, _run_claude_cli(), _sanitize_plan_output(), _validate_request(), CodexProvider, _run_cli(), ProviderSelection (+27 more)

### Community 5 - "Config & Data Models"
Cohesion: 0.07
Nodes (37): BaseModel, CloudWatchLoggingHandler, FileLoggingHandler, LoggingConfig, LoggingHandlerBase, LoopConfig, OutputConfig, ProviderModes (+29 more)

### Community 6 - "Provider Protocol & Direction"
Cohesion: 0.09
Nodes (17): build_summary(), ProviderAdapter, ProviderResponse, DirectionService, FakeProvider, Protocol, GET(), _non_kept_streak() (+9 more)

### Community 7 - "Validation & Error Handling"
Cohesion: 0.11
Nodes (20): validate_manifest(), GoalseekError, ManifestValidationError, MetricExtractionError, Base class for package errors., ScopeViolationError, VerificationError, Exception (+12 more)

### Community 8 - "CLI Rich Rendering"
Cohesion: 0.12
Nodes (18): failure(), _pretty_label(), render_baseline(), render_direction(), render_generic(), render_kv_table(), render_project_init(), render_run() (+10 more)

### Community 9 - "GoalSeek Algorithm Diagram"
Cohesion: 0.35
Nodes (12): Adjust Input, Calculate Output, Compare & Evaluate, Computation, Define Problem, GoalSeek Iteration Loop, Initial Guess, Input Variable (+4 more)

### Community 10 - "Sidebar Navigation UI"
Cohesion: 0.22
Nodes (2): SidebarMenuButton(), useSidebar()

### Community 11 - "Toast Notification System"
Cohesion: 0.57
Nodes (6): addToRemoveQueue(), dispatch(), genId(), reducer(), toast(), useToast()

### Community 12 - "App Icon SVG"
Cohesion: 0.39
Nodes (8): Adaptive Color Scheme (Dark/Light Mode), GoalSeek App Icon, Left Glyph Path (Y-like shape), GoalSeek Logomark (GS Brand Symbol), Right Glyph Path (S/Z-like shape), Rounded Rectangle Background Shape, SVG Vector Format, Web Public Assets Directory

### Community 13 - "Alert Dialog Component"
Cohesion: 0.29
Nodes (0): 

### Community 14 - "Breadcrumb Navigation"
Cohesion: 0.29
Nodes (0): 

### Community 15 - "Context Menu Component"
Cohesion: 0.29
Nodes (0): 

### Community 16 - "Pagination Component"
Cohesion: 0.29
Nodes (0): 

### Community 17 - "Select Dropdown"
Cohesion: 0.29
Nodes (0): 

### Community 18 - "Kaggle ML Experiment"
Cohesion: 0.4
Nodes (5): build_pipeline(), Baseline Logistic Regression model for Irrigation Need prediction.  Responsibi, Return an unfitted Logistic Regression pipeline., Load training data, fit the pipeline, persist to *model_path*., train()

### Community 19 - "Sheet Component"
Cohesion: 0.33
Nodes (0): 

### Community 20 - "Run List View"
Cohesion: 0.4
Nodes (0): 

### Community 21 - "Carousel Component"
Cohesion: 0.5
Nodes (2): CarouselNext(), useCarousel()

### Community 22 - "Drawer Component"
Cohesion: 0.4
Nodes (0): 

### Community 23 - "Dropdown Menu"
Cohesion: 0.4
Nodes (0): 

### Community 24 - "Form Component"
Cohesion: 0.4
Nodes (0): 

### Community 25 - "Folder Picker Dialog"
Cohesion: 0.5
Nodes (0): 

### Community 26 - "Metric Chart View"
Cohesion: 0.67
Nodes (2): CustomTooltip(), getStatusColor()

### Community 27 - "Run Detail Panel"
Cohesion: 0.5
Nodes (0): 

### Community 28 - "Card Component"
Cohesion: 0.5
Nodes (0): 

### Community 29 - "OTP Input Component"
Cohesion: 0.5
Nodes (0): 

### Community 30 - "Item Component"
Cohesion: 0.5
Nodes (0): 

### Community 31 - "Menubar Component"
Cohesion: 0.5
Nodes (0): 

### Community 32 - "Navigation Menu"
Cohesion: 0.5
Nodes (0): 

### Community 33 - "Toggle Group"
Cohesion: 0.5
Nodes (0): 

### Community 34 - "Tooltip Component"
Cohesion: 0.5
Nodes (0): 

### Community 35 - "Apple Touch Icon Assets"
Cohesion: 0.83
Nodes (4): Apple Touch Icon (GoalSeek), GoalSeek Brand / Logo Mark, GoalSeek Web Application, Web Public Static Assets

### Community 36 - "Dark Theme Icon"
Cohesion: 0.5
Nodes (4): App Dark Icon (32x32), Dark Theme Variant, Favicon / Browser Tab Icon, VIO / V10 Logo Mark

### Community 37 - "Light Theme Icon"
Cohesion: 0.83
Nodes (4): GoalSeek App Icon (Light, 32x32), Light Theme Icon Variant, Web Public Static Asset, v0 Logotype

### Community 38 - "Diff Viewer Component"
Cohesion: 0.67
Nodes (0): 

### Community 39 - "Project Header View"
Cohesion: 0.67
Nodes (0): 

### Community 40 - "Alert Component"
Cohesion: 0.67
Nodes (0): 

### Community 41 - "Avatar Component"
Cohesion: 0.67
Nodes (0): 

### Community 42 - "Chart Utilities"
Cohesion: 0.67
Nodes (0): 

### Community 43 - "Collapsible Component"
Cohesion: 0.67
Nodes (0): 

### Community 44 - "Radio Group"
Cohesion: 0.67
Nodes (0): 

### Community 45 - "Scroll Area"
Cohesion: 0.67
Nodes (0): 

### Community 46 - "Slider Component"
Cohesion: 0.67
Nodes (0): 

### Community 47 - "Tabs Component"
Cohesion: 0.67
Nodes (0): 

### Community 48 - "Mobile Detection Hook"
Cohesion: 0.67
Nodes (1): useIsMobile()

### Community 49 - "CLI Entry Point"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Test Package Setup"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Test Package Init"
Cohesion: 1.0
Nodes (1): Test package marker for intra-test imports.

### Community 52 - "Next.js Root Layout"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Web Home Page"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Runs API Route"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Theme Provider"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Demo Explorer"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Accordion Component"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Badge Component"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Button Group"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Button Component"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Calendar Component"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Checkbox Component"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Command Component"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Dialog Component"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Empty State"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Field Component"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Hover Card"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Input Group"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Keyboard Shortcut Display"
Cohesion: 1.0
Nodes (0): 

### Community 70 - "Label Component"
Cohesion: 1.0
Nodes (0): 

### Community 71 - "Separator Component"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Skeleton Loader"
Cohesion: 1.0
Nodes (0): 

### Community 73 - "Sonner Toast"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Switch Component"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Textarea Component"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Docs Site Config"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Docs Sidebars"
Cohesion: 1.0
Nodes (0): 

### Community 78 - "Docs Index Page"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Next.js Type Defs"
Cohesion: 1.0
Nodes (0): 

### Community 80 - "Artifact Viewer"
Cohesion: 1.0
Nodes (0): 

### Community 81 - "Aspect Ratio"
Cohesion: 1.0
Nodes (0): 

### Community 82 - "Input Component"
Cohesion: 1.0
Nodes (0): 

### Community 83 - "Popover Component"
Cohesion: 1.0
Nodes (0): 

### Community 84 - "Progress Component"
Cohesion: 1.0
Nodes (0): 

### Community 85 - "Resizable Layout"
Cohesion: 1.0
Nodes (0): 

### Community 86 - "Spinner Component"
Cohesion: 1.0
Nodes (0): 

### Community 87 - "Toast Component"
Cohesion: 1.0
Nodes (0): 

### Community 88 - "Toaster Component"
Cohesion: 1.0
Nodes (0): 

### Community 89 - "Toggle Component"
Cohesion: 1.0
Nodes (0): 

### Community 90 - "Placeholder Logo Triangle"
Cohesion: 1.0
Nodes (1): Placeholder Logo (Dotted Triangle)

### Community 91 - "Placeholder Logo Acme"
Cohesion: 1.0
Nodes (1): Placeholder Logo (Acmelnc Brand Template)

### Community 92 - "Placeholder User Avatar"
Cohesion: 1.0
Nodes (1): Placeholder User Avatar

### Community 93 - "Placeholder Image"
Cohesion: 1.0
Nodes (1): Placeholder Image

### Community 94 - "Placeholder Image 2"
Cohesion: 1.0
Nodes (1): Placeholder Image

## Knowledge Gaps
- **34 isolated node(s):** `Base class for package errors.`, `Baseline Logistic Regression model for Irrigation Need prediction.  Responsibi`, `Return an unfitted Logistic Regression pipeline.`, `Load training data, fit the pipeline, persist to *model_path*.`, `Validation script for the Irrigation Need baseline model.  Responsibilities:` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `CLI Entry Point`** (2 nodes): `cli()`, `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Package Setup`** (2 nodes): `main()`, `setup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Package Init`** (2 nodes): `Test package marker for intra-test imports.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Next.js Root Layout`** (2 nodes): `RootLayout()`, `layout.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Web Home Page`** (2 nodes): `HomePage()`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Runs API Route`** (2 nodes): `POST()`, `route.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Theme Provider`** (2 nodes): `ThemeProvider()`, `theme-provider.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Demo Explorer`** (2 nodes): `fetcher()`, `demo-explorer.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Accordion Component`** (2 nodes): `Accordion()`, `accordion.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Badge Component`** (2 nodes): `Badge()`, `badge.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Button Group`** (2 nodes): `cn()`, `button-group.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Button Component`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Calendar Component`** (2 nodes): `cn()`, `calendar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Checkbox Component`** (2 nodes): `Checkbox()`, `checkbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Command Component`** (2 nodes): `cn()`, `command.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dialog Component`** (2 nodes): `cn()`, `dialog.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Empty State`** (2 nodes): `cn()`, `empty.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Field Component`** (2 nodes): `cn()`, `field.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Hover Card`** (2 nodes): `HoverCardTrigger()`, `hover-card.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Input Group`** (2 nodes): `cn()`, `input-group.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Keyboard Shortcut Display`** (2 nodes): `cn()`, `kbd.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Label Component`** (2 nodes): `Label()`, `label.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Separator Component`** (2 nodes): `Separator()`, `separator.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Skeleton Loader`** (2 nodes): `Skeleton()`, `skeleton.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sonner Toast`** (2 nodes): `Toaster()`, `sonner.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Switch Component`** (2 nodes): `Switch()`, `switch.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Textarea Component`** (2 nodes): `cn()`, `textarea.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Docs Site Config`** (1 nodes): `docusaurus.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Docs Sidebars`** (1 nodes): `sidebars.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Docs Index Page`** (1 nodes): `index.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Next.js Type Defs`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Artifact Viewer`** (1 nodes): `artifact-viewer.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Aspect Ratio`** (1 nodes): `aspect-ratio.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Input Component`** (1 nodes): `input.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Popover Component`** (1 nodes): `popover.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Progress Component`** (1 nodes): `progress.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Resizable Layout`** (1 nodes): `resizable.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Spinner Component`** (1 nodes): `spinner.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Toast Component`** (1 nodes): `toast.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Toaster Component`** (1 nodes): `toaster.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Toggle Component`** (1 nodes): `toggle.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Placeholder Logo Triangle`** (1 nodes): `Placeholder Logo (Dotted Triangle)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Placeholder Logo Acme`** (1 nodes): `Placeholder Logo (Acmelnc Brand Template)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Placeholder User Avatar`** (1 nodes): `Placeholder User Avatar`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Placeholder Image`** (1 nodes): `Placeholder Image`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Placeholder Image 2`** (1 nodes): `Placeholder Image`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LoopEngine` connect `Core Loop Engine` to `CLI Command Layer`, `Git Ops & Configuration`, `Claude Code Provider`, `Config & Data Models`, `Provider Protocol & Direction`, `Validation & Error Handling`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `invoke()` connect `CLI Command Layer` to `CLI Rich Rendering`, `Core Loop Engine`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `info()` connect `Core Loop Engine` to `CLI Command Layer`, `Git Ops & Configuration`, `Claude Code Provider`, `Provider Protocol & Direction`, `CLI Rich Rendering`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `str` (e.g. with `init_project()` and `get_status()`) actually correct?**
  _`str` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `LoopEngine` (e.g. with `ArtifactStore` and `ContextReader`) actually correct?**
  _`LoopEngine` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Repo` (e.g. with `ContextReader` and `LoopEngine`) actually correct?**
  _`Repo` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `ClaudeCodeProvider` (e.g. with `ProviderSelection` and `ProviderCapabilities`) actually correct?**
  _`ClaudeCodeProvider` has 27 INFERRED edges - model-reasoned connections that need verification._