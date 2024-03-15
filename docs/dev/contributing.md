# Contributing to the App

The project is packaged with a light [development environment](dev_environment.md) based on `docker-compose` to help with the local development of the project and to run tests.

The project is following Network to Code software development guidelines and is leveraging the following:

- Python linting and formatting: `black`, `pylint`, `bandit`, `flake8`, and `ruff`.
- YAML linting is done with `yamllint`.
- Django unit test to ensure the app is working properly.

Documentation is built using [mkdocs](https://www.mkdocs.org/). The [Docker based development environment](dev_environment.md#docker-development-environment) automatically starts a container hosting a live version of the documentation website on [http://localhost:8001](http://localhost:8001) that auto-refreshes when you make any changes to your local files.

## Creating Changelog Fragments

All pull requests to `next` or `develop` must include a changelog fragment file in the `./changes` directory. To create a fragment, use your GitHub issue number and fragment type as the filename. For example, `2362.added`. Valid fragment types are `added`, `changed`, `deprecated`, `fixed`, `removed`, and `security`. The change summary is added to the file in plain text. Change summaries should be complete sentences, starting with a capital letter and ending with a period, and be in past tense. Each line of the change fragment will generate a single change entry in the release notes. Use multiple lines in the same file if your change needs to generate multiple release notes in the same category. If the change needs to create multiple entries in separate categories, create multiple files.

!!! example

    **Wrong**
    ```plaintext title="changes/1234.fixed"
    fix critical bug in documentation
    ```

    **Right**
    ```plaintext title="changes/1234.fixed"
    Fixed critical bug in documentation.
    ```

!!! example "Multiple Entry Example"

    This will generate 2 entries in the `fixed` category and one entry in the `changed` category.

    ```plaintext title="changes/1234.fixed"
    Fixed critical bug in documentation.
    Fixed release notes generation.
    ```

    ```plaintext title="changes/1234.changed"
    Changed release notes generation.
    ```

## Branching Policy

The branching policy includes the following tenets:

- The `develop` branch is the branch of the next major and minor paired version planned.
- PRs intended to add new features should be sourced from the `develop` branch.
- PRs intended to fix issues in the Nautobot LTM compatible release should be sourced from the latest `ltm-<major.minor>` branch instead of `develop`.

Golden Config will observe semantic versioning, as of 1.0. This may result in a quick turnaround in minor versions to keep pace with an ever-growing feature set.

## Release Policy

Golden Config has currently no intended scheduled release schedule, and will release new features in minor versions.

When a new release, from `develop` to `main`, is created the following should happen.

- A release PR is created from `develop` with:
    - Update the release notes in `docs/admin/release_notes/version_<major>.<minor>.md` file to reflect the changes.
    - Change the version from `<major>.<minor>.<patch>-beta` to `<major>.<minor>.<patch>` in `pyproject.toml`.
    - Set the PR to the `main` branch.
- Ensure the tests for the PR pass.
- Merge the PR.
- Create a new tag:
    - The tag should be in the form of `v<major>.<minor>.<patch>`.
    - The title should be in the form of `v<major>.<minor>.<patch>`.
    - The description should be the changes that were added to the `version_<major>.<minor>.md` document.
- If merged into `main`, then push from `main` to `develop`, in order to retain the merge commit created when the PR was merged
- A post release PR is created with:
    - Change the version from `<major>.<minor>.<patch>` to `<major>.<minor>.<patch + 1>-beta` in both `pyproject.toml` and `nautobot.__init__.__version__`.
    - Set the PR to the proper branch, `develop`.
    - Once tests pass, merge.
