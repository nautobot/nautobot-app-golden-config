# Navigating Config Plans

The natural progression for the Golden Config application is providing the ability to execute config deployments. One specific example is to work toward making one or more devices configuration compliant. To aid in this effort, the Golden Config application has the ability to generate plans containing sets of configuration commands from various sources with the intent of deploying them to devices.

The current sources of these plans (i.e. plan types) are as follows:

- The **Intended** configuration(s) of Compliance Feature(s)
- The **Missing** configuration(s) of Compliance Feature(s)
- The **Remediation** configuration(s) of Compliance Feature(s) (*)
- A **Manual** set of configuration commands

!!! note
    The Intended, Missing and Remediation configuration come from the [Configuration Compliance](./app_feature_compliance.md#compliance-details-view) object that is created when you run the [Perform Configuration Compliance Job](./app_feature_compliance.md#starting-a-compliance-job).

Much like a Configuration Compliance object, each Config Plan is tied directly to a single Device.

## Viewing a Config Plan

You can view a plan by navigating to **Golden Config -> Config Plans** and choosing a generated plan from the list. A Config Plan comprises of the following fields:

- **Device**: The device the plan is to be deployed to.
- **Date Created**: The date the plan was generated.
- **Plan Type**: The type of plan used to generate it.
- **Config Set**: The set of commands to be deployed.
- **Features** (If Applicable): The Compliance Feature(s) the config set was generated from.
- **Change Control ID** (Optional): A text field that be used for grouping and filtering plans.
- **Change Control URL** (Optional): A URL field that can be used to link to an external system tracking change controls.
- **Job Result**: The Job that generated the plan(s).
- **Status**: The status of the plan. See [Approving Config Plans](#approving-config-plans) for how approval is reflected in the status.
- **Approval State** (If Applicable): The state of the plan's Approval Workflow (`Pending`, `Approved`, `Denied` or `Canceled`). It is empty when the plan is approved by status.

![Config Plan View](../images/ss1_config_plan-view_light.png#only-light){ .on-glb }
![Config Plan View](../images/ss1_config_plan-view_dark.png#only-dark){ .on-glb }

## Generating Config Plans

In order to generate a plan, navigate to **Golden Config -> Config Plans** and hit the **Add** button. After choosing the type of plan you want to generate, you can then filter the list of devices you want to generate a Config Plan for by selecting either the list of devices themselves or a by choosing one or more related items such as Location or Status. If you select a plan type that is derived from a Configuration Compliance object, you will have the ability to only generate plans for one or more features, but selecting no features will generate plans for all applicable features.

In addition, you have the ability to specify a Change Control ID & URL that can be associated with all of the plans that will be generated. This can come in handy when it comes to filtering the list of plans to ultimately deploy.

Once you have selected the appropriate options, you can click the **Generate** button which will start a Job to generate the plans.

### Screenshots

![Config Plan Generate Missing](../images/ss1_config_plan-generate-missing_light.png#only-light){ .on-glb }
![Config Plan Generate Missing](../images/ss1_config_plan-generate-missing_dark.png#only-dark){ .on-glb }

![Config Plan Generate Filters](../images/ss1_config_plan-generate-filters_light.png#only-light){ .on-glb }
![Config Plan Generate Filters](../images/ss1_config_plan-generate-filters_dark.png#only-dark){ .on-glb }

![Config Plan Generate Manual](../images/ss1_config_plan-generate-manual_light.png#only-light){ .on-glb }
![Config Plan Generate Manual](../images/ss1_config_plan-generate-manual_dark.png#only-dark){ .on-glb }

### Generating Config Plans via API

The HTTP(S) POST method is not currently enabled for the Config Plan serializer to create plans directly via API. Instead you may run the **Generate Config Plans** Job directly via the `/api/extras/jobs/Generate Config Plans/run/` API endpoint.

## Editing a Config Plan

After a Config Plan is generated you have the ability to edit (or bulk edit) the following fields:

- Change Control ID
- Change Control URL
- Status (unless the plan has an Approval Workflow, which manages the status)
- Notes
- Tags

!!! note
    You will not be able to modify the Config Set after generation. If it does not contain the desired commands, you will need to delete the plan and recreate it after ensuring the source of the generated commands has been updated.

![Config Plan Edit](../images/ss1_config_plan-edit_light.png#only-light){ .on-glb }
![Config Plan Edit](../images/ss1_config_plan-edit_dark.png#only-dark){ .on-glb }

If the Config Plan has post processing functions, you can render the post processed config to validate and approve a Config Plan.

![Config Plan Post Processing Button](../images/ss1_config_plan_pp_button_light.png#only-light){ .on-glb }
![Config Plan Post Processing Button](../images/ss1_config_plan_pp_button_dark.png#only-dark){ .on-glb }

Post Processing occurs in a modal popup, and allows a user to view the configuration before approving the Config Plan.

![Intended Configuration Web UI](../images/ss1_config_plan_pp-rendered_light.png#only-light){ .on-glb }
![Intended Configuration Web UI](../images/ss1_config_plan_pp-rendered_dark.png#only-dark){ .on-glb }

## Approving Config Plans

A Config Plan can only be deployed once it is approved. There are two ways to approve a plan, chosen per [Golden Config Setting](./app_getting_started.md), so devices in different scopes can use different methods.

### Approval by Status

This is the default. New plans are created with the status set by the `default_deploy_status` [app setting](../admin/install.md#app-configuration) (`Not Approved`), and the **Deploy Config Plans** job refuses to run for them. A user approves a plan by editing it, or bulk editing several plans, and setting the status to `Approved`.

### Approval by Approval Workflow

This is the **single config plan approval workflow** model: a Config Plan belongs to one device, so every plan gets its own workflow and is approved on its own. Generating plans for 50 devices creates 50 workflows, and approvers handle each one separately. Nothing groups the plans from one Generate Config Plans run under a shared approval.

If the Golden Config Setting that applies to a device has a **Config Plan Approval Workflow** selected, each plan generated for that device starts a Nautobot [Approval Workflow](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/approval-workflow/) from that definition. The status of the plan follows the workflow, and users can no longer edit it by hand:

| Approval Workflow | Config Plan Status |
| ----------------- | ------------------ |
| Started           | `Pending Approval` |
| Approved (every stage approved) | `Approved` |
| Denied by an approver | `Not Approved` |
| Canceled | `Not Approved` |

Once the deployment starts, the status follows the deployment (`In Progress`, then `Completed` or `Failed`) and approval outcomes no longer change it.

The **Deploy Config Plans** job always fails, and deploys nothing for any plan in the batch, if any plan with an approval workflow is not `Approved`. The job result lists the plans that are not approved. See [E3025](../admin/troubleshooting/E3025.md).

#### Setting Up an Approval Workflow

1. Create a group for the approvers and add the users to it.
2. Under **Extras -> Approval Workflow Definitions**, add a definition whose **Model content type** is `nautobot_golden_config | config plan`, and give it one or more stages that use the approver group.
3. Edit the Golden Config Setting and select the definition for **Config Plan Approval Workflow**. A definition without stages is rejected.

A definition only takes effect when a Golden Config Setting selects it, and a definition that a setting selects cannot be deleted. Changing the selection only affects plans generated afterwards.

!!! warning
    A device is only ever generated under one Golden Config Setting: the one with the highest weight among the settings whose scope includes the device. A plan gets an approval workflow only if that setting selects one.

    If a device is also in the scope of another setting, for example the **Default Settings** whose scope matches every device on a new install, give the setting that selects the workflow a strictly higher weight. With equal weights the setting that applies is not guaranteed, and the plan is generated without a workflow and approved by status instead. Plans do not pick up a workflow later, so delete and generate them again after correcting the weights.

Approvers need these permissions:

- `extras.view_approvalworkflowstage` and `extras.change_approvalworkflowstage`, to see and approve stages.
- `nautobot_golden_config.view_configplan`, to read the config set they are approving.
- `nautobot_golden_config.change_configplan`, to approve through the REST API, which checks `change` permission on the object under review. Approving in the web UI does not need it.

Approvers find the plans waiting for them on the **Approver Dashboard** under **Extras -> Approval Workflows**.

#### Resubmitting a Denied Plan

A denied or canceled workflow is finished and cannot be reopened by an approver. If the plan can still be used, for example when it was denied for a missing Change Control ID that has since been added, a user with the `change_configplan` permission selects **Resubmit for Approval** on the plan, or sends a POST to `/api/plugins/golden-config/config-plan/<id>/resubmit/`.

This starts a new round of review on the same workflow: every stage and response goes back to pending, the comments are kept, and the status returns to `Pending Approval`. Approvers who denied the plan can then approve it. Earlier approvals do not carry over.

A plan cannot be resubmitted once its deployment has started or if the approval workflow definition was deleted. Because the Config Set cannot be modified after generation, a plan that was denied for its commands should be deleted and generated again after the source of the commands has been corrected.

#### Removing the Approval Workflow

Plans keep the workflow they were created with. If an administrator deletes the workflow of a plan, the plan falls back to approval by status. Its status is editable again, and it stays `Not Approved` or `Pending Approval` until a user changes it.

!!! warning
    Deleting an Approval Workflow Definition that existing plans still use leaves those plans with a workflow that can no longer be approved. Delete the workflows of those plans to return them to approval by status.
