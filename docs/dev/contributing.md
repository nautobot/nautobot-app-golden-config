# Contributing to the App

The project is packaged with a light [development environment](dev_environment.md) based on `docker-compose` to help with the local development of the project and to run tests.

The project is following Network to Code software development guidelines and is leveraging the following:

- Python linting and formatting: `pylint` and `ruff`.
- YAML linting is done with `yamllint`.
- Django unit test to ensure the app is working properly.
- Django Template linting: `djlint`
- Django Template formatting: `djhtml`

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

### Backporting to Older Releases

If you are backporting any fixes to a prior major or minor version of this app, please open an issue, comment on an existing issue, or post in the [Network to Code Slack](https://networktocode.slack.com/) (channel `#nautobot`).

We will create a `release-X.Y` branch for you to open your PR against and cut a new release once the PR is successfully merged.

## Release Policy

Golden Config has currently no intended scheduled release schedule, and will release new features in minor versions.

The steps taken by maintainers when creating a new release are documented in the [release checklist](./release_checklist.md).
