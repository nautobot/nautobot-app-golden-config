# Contributing to the App

The project is packaged with a light [development environment](dev_environment.md) based on `docker-compose` to help with the local development of the project and to run tests.

The project is following Network to Code software development guidelines and is leveraging the following:

- Black, Pylint, Bandit, flake8, yamllint, and pydocstyle for Python linting and formatting.
- Django unit test to ensure the plugin is working properly.

Documentation is built using [mkdocs](https://www.mkdocs.org/). The [Docker based development environment](dev_environment.md#docker-development-environment) automatically starts a container hosting a live version of the documentation website on [http://localhost:8001](http://localhost:8001) that auto-refreshes when you make any changes to your local files.

## Branching Policy

The branching policy includes the following tenets:

- The `develop` branch is the branch for bug fixes.
- The `next` branch is the branch for new features.
- The `stable-<major>.<minor>` branch is the branch of the latest version within that major/minor version.
- The `stable-<major>.<minor>` branch will have all of the latest bug fixes and security patches, and may or may not represent the released version.
- PRs intended to add new features should be branched from and merged to the `next` branch.
- PRs intended to add new features that break backward compatibility should be discussed before a PR is created.
- PRs intended to address bug fixes and security patches should be branched from and merged to the `develop` branch.

Nautobot Golden Config will observe semantic versioning, as of 1.0. This may result in an quick turn around in minor versions to keep pace with an ever growing feature set.

## Release Policy

Nautobot Golden Config has currently no intended scheduled release schedule, and will release new features in minor versions.

When a new release of any kind (e.g. from `develop` to `main`, or a release of a `stable-<major>.<minor>`) is created the following should happen.

- A release PR is created:
    - Add and/or update to the changelog in `docs/admin/release_notes/version_<major>.<minor>.md` file to reflect the changes.
    - Update the mkdocs.yml file to include updates when adding a new release_notes version file.
    - Change the version from `<major>.<minor>.<patch>-beta` to `<major>.<minor>.<patch>` in pyproject.toml.
    - Set the PR to the proper branch, e.g. either `main` or `stable-<major>.<minor>`.
- Ensure the tests for the PR pass.
- Merge the PR.
- Create a new tag:
    - The tag should be in the form of `v<major>.<minor>.<patch>`.
    - The title should be in the form of `v<major>.<minor>.<patch>`.
    - The description should be the changes that were added to the `version_<major>.<minor>.md` document.
- If merged into `main`, then push from `main` to `develop`, in order to retain the merge commit created when the PR was merged.
- If the is a new `<major>.<minor>`, create a `stable-<major>.<minor>` for the **previous** version, so that security updates to old versions may be applied more easily.
- A post release PR is created:
    - Change the version from `<major>.<minor>.<patch>` to `<major>.<minor>.<patch + 1>-beta` in pyproject.toml.
    - Set the PR to the proper branch, e.g. either `develop` or `stable-<major>.<minor>`.
    - Once tests pass, merge.
