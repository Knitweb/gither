# Agent Profile

This is the recommended engineering profile for agents working inside Forge-managed
workspaces.

## Writing

- Do not use the em dash character.
- Do not auto-add an agent name as a commit co-author.
- Do not manually modify generated changelogs.
- Put each full sentence on its own physical line in long Markdown files.
- Preserve normal Markdown structure.

## Engineering

- Prefer quality, simplicity, robustness, scalability, and long-term maintainability.
- Start bug fixes by reproducing the bug as close to the end-user path as possible.
- Treat lint, test failures, and flaky tests as real issues.
- Keep changes scoped to the routed repository unless the contract requires broader work.
- Run repo-local tests before widening to cross-repo tests.

## UI

- Be picky about visible UI.
- Check spacing, overlap, labels, and mobile layout.
- Fix obviously broken UI if it is in the touched surface.

## Multi-Repo Discipline

- Route first with Forge.
- Read the selected repo docs.
- Make the change.
- Run selected repo tests.
- Run the Forge test plan if shared contracts changed.
- Update the workspace manifest if repository ownership changed.
