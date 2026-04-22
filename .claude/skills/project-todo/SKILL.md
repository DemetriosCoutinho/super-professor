---
name: project-todo
description: Manage PROJECT_TODO.md — add, complete, block, promote, and archive tasks. Replicable: this skill reads/writes only PROJECT_TODO.md and works in any repo that has that file.
disable-model-invocation: true
---

You are managing `PROJECT_TODO.md` in the current working directory.

## Commands

The user invokes `/project-todo <command> [args]`. Parse the command from the skill arguments.

| Command | Syntax | Action |
|---------|--------|--------|
| `add` | `add <section> <text>` | Add a new `- [ ] <text>` to the named section |
| `done` | `done <partial text>` | Move matching item to Done with today's date |
| `block` | `block <partial text> — <reason>` | Move matching item to Blocked, append `— bloqueio: <reason>` |
| `promote` | `promote <partial text>` | Move matching item from Next → Now, add `started <today>` |
| `archive` | `archive` | Move Done items older than 14 days to CHANGELOG.md (append) or done-archive-YYYY-MM.md |
| `list` | `list` or no args | Print the full PROJECT_TODO.md content |

## Steps

1. Read `PROJECT_TODO.md`.
2. Apply the requested mutation.
3. Update the `> Última atualização:` date to today.
4. Write the file back.
5. Confirm to the user: "PROJECT_TODO.md atualizado — `<section>`: `<item>`."

## Sections

Valid section names (case-insensitive, accept Portuguese or English):
- `now` / `em andamento`
- `next` / `próximas`
- `later` / `backlog`
- `blocked` / `bloqueado`

Default section for `add` when not specified: `next`.

## GUARDRAILS

- NEVER delete items — only move them between sections or to archive
- NEVER modify any file other than `PROJECT_TODO.md` (and CHANGELOG.md or done-archive-YYYY-MM.md for `archive`)
- If `PROJECT_TODO.md` does not exist: create it using the standard template (Now / Next / Later / Blocked / Done sections) with empty lists, then apply the command
- If the command is ambiguous (multiple partial matches), list the matches and ask the user to be more specific
