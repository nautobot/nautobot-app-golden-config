# Configuration Generation


## Installation Instructions

## Intended Configuration Settings

In order to generate the intended configurations two repositories are needed.

1. A repo to save intended configurations to once generated. [See](#Configs-Repository)
2. A repo that stores Jinja2 templates used to generate intended configurations. [See](#Templates-Repository)

### Configs Repository
The first step is to go to Nautobot and navigate to the Data Sources Git integration. `Extensibility -> Git Repositories`.

![Intended Git Navigation](./img/git-step1.png)

From the Git Repositories page we an add the **configs** repository.

Click on `[+ADD]`.

You will now be presented with a page to fill in the repository details.

Parameters:
|Field|Explanation|
|:--|:--|
|Name|User friendly name for the backup repo.|
|Slug|Auto-generated based on the `name` provided.|
|Remote URL|The URL pointing to the Git repo that stores the backup configuration files. Current git url usage is limited to `http` or `https`.|
|Branch|The branch in the Git repo to use. Defaults to `main`.|
|Token|The token is a personal access token for the `username` provided.  For more information on generating a personal access token. [Github Personal Access Token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
|Username|The Git username that corresponds with the personal access token above.|
|Provides|Valid providers for Git Repo.|
<br>

![Example Git Intended](./img/intended-git-step2.png)

Select `backup configs` and click on `[Create]`.

Once you click `[Create]` and the repository syncs, the main page will now show the repo along with its status.

### Templates Repository
Navigate back to Git Repositories and click `[+ADD]`.  Fill out the form with the repo that holds the Jinja2 templates.

![Example Git Templates](./img/templates-git-step2.png)

Select `jinja templates` and click on `[Create]`.

Next, it is necessary to configure the settings for the [intended path](./golden-config-settings.md#Intended-Path), and [template path](./golden-config-settings.md#Template-Path).
