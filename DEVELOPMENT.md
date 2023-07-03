# Development notes

## How to make releases

- Mark release in `CHANGELOG.md`.
- Make a new commit and tag it with `vX.Y.Z`.
- Prepare update for templates repository and make sure it all works.
- Trigger the PyPI GitHub Action: `git push origin main --tags`.
- Commit and push changes to templates repository.
