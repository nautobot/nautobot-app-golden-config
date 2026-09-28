# Frequently Asked Questions

## _Why doesn't the compliance behavior work the way I expected it to?_

There are many ways to consider golden configs as shown in this [blog](https://blog.networktocode.com/post/journey-in-golden-config/). We cannot provide accommodations for all versions as it will both bloat the system, create a more complex system, and ultimately run into conflicting interpretations. Keeping the process focused but allowing anyone to override their interpretation of how compliance should work is both a powerful (via sane defaults) and complete (via custom compliance) solution.

Any other interpretations of how compliance should be viewed are encouraged to use custom compliance option.

## _Why don't the configurations match like the vendor cli?_

A vendor processes configuration understanding constructs such as knowing that `int g0/0` and `interface GigabitEthernet0/0` are the same. Each one of these rules a subject to a given vendor's OS implementation. The ability to track these changes for all vendors/OS/versions is nearly impossible. Additionally, this practice would be error prone and not follow the principal of least astonishment. Notwithstanding a major change in the network industry, adjusting this strategy is outside the scope of the app.

Instead, the operator is required to ensure their configurations match exactly as the configurations show in the running configuration. This includes all spacing, special characters, or literally anything that result in a string comparison not returning true.

Any other interpretations of how compliance should be viewed are encouraged to use custom compliance option.

## _Why doesn't the config overview page reflect the inclusion changes immediately?_

On a technical level, those changes enable the model `GoldenConfig` to *not* filter out the newly included devices, but this does not add to the model. In order to be included, a new job needs to be ran which will create an entry within `GoldenConfig`, any of the 3 jobs that successfully run will create such an entry.

## _Why aren't configurations generated or compliance generated real time?_

The app make no assumptions about your intention and expects the operator to manage the configurations as they see fit. As as example, in preparation for a change, one may update data to reflect these changes, but not want to generate or run compliance against these configurations.

Additionally, configurations generated would have to either update the Git Repo immediately or generate locally only and not update the Git Repo, both of which may not be as the user expected.

The current design allows for the maximum amount of use cases and make little assumptions how the user wants to manage their configurations. That being said, education about how the process works is important as inevitably any design choice will not be line with another person's pre-conceived notions. There are a myriad of technical issues to be considered before any change can be made to this process.

## _Why not predefine a list of remove and substitute lines within backup configurations?_

Backup configurations solutions are simple to start with and grow to hundreds or thousands of requests. That added complexity is not something that is in scope for the project.

Many people will have different opinions about what should or should not be filtered or substituted. Providing the flexibility allows the user to have it operate as they intend it, without burdening the apps goals.

## _Is it safe to store backup configurations in Git? My security team has concerns._

This question comes up regularly, so it is worth addressing the design directly. Backup configurations are stored in a Git repository; there is no alternative backup backend, and adding one is not in scope. Note that "Git" here means the version-control system, not a specific hosted service such as GitHub or GitLab. You can run your own Git server entirely inside your infrastructure, giving you full control over access, including allowing no external access at all. The right conversation is therefore not "Git versus something else," but how the repository is hosted, who can read it, and how sensitive content is handled before it is committed.

A few points worth understanding before the discussion:

* **Sanitization is operator-defined and best-effort.** The `Config Removals` and `Config Replacements` settings let you strip or substitute sensitive lines per-platform, but they are regex rules you maintain. They are only as complete as the patterns you write. A pattern that misses a secret will commit that secret.
* **Git history is durable.** A configuration committed to Git remains in history even after the file is changed or deleted. Removing a file in a later commit does not remove it from the repository's history. Treat anything ever committed as retained unless history is deliberately rewritten.
* **The configuration is not only in Git.** A successful backup also populates the `backup_config` field on the `GoldenConfig` model in the database, and compliance compares the database copy of the backup and intended configurations, not the files on disk. The Git repository is the versioned store; it is not the only place the configuration data exists.

Because of the last point, deleting backup files from Git after a compliance run does not remove the configuration from the system, and the next backup run will repopulate and recommit it. That approach adds churn without achieving the intended outcome.

For environments with strict requirements, the recommended approach is to keep using Git but control where it lives: a self-hosted or otherwise private, internally hosted repository with role-based access, encryption at rest, audit logging, and no external mirror, combined with thorough `Config Removals` and `Config Replacements` rules for your platforms. Repository-level secret scanning or push protection, offered by most Git hosts, is a worthwhile additional layer, since it can catch credentials that a removal or replacement pattern misses. Together these satisfy the large majority of security reviews without working against the app's design.

## _Why not predefine the configuration feature map?_

The process is based on an opinion on what defines a feature, for one organization BGP may include the prefix configuration and another it would not.

Understanding that there will never be consensus on what should go into a feature it becomes obvious why the users must maintain such configuration.

## _What are the supported platforms for Compliance jobs? How do I configure a device with a specific OS?_

The current supported platform and the associated *default* platform network_driver names are the following for:

* arista_eos
* aruba_aoscx
* bigip_f5
* cisco_aireos
* cisco_asa
* cisco_ios
* cisco_ios_xr
* citrix_netscaler
* cisco_nxos
* extreme_netiron
* fortinet_fortios
* juniper_junos
* linux
* mikrotik_routeros
* mrv_optiswitch
* nokia_sros
* paloalto_panos

The expected "network_os" parameter must be set using the platform `network_driver`, which then in turn provides you the `network_driver_mappings` to map out the framework, such as netmiko and napalm. This should solve most use cases, but occasionally you may want to extend this mapping, for further understand see [the docs](https://docs.nautobot.com/projects/core/en/stable/user-guide/core-data-model/dcim/platform/) and simply update the [NETWORK_DRIVER](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/configuration/optional-settings/#network_drivers) configuration.

Here is an example Device object representation, e.g. `device.platform.network_driver_mappings` to help provide some context.

```python
{
    "ansible": "cisco.nxos.nxos",
    "hier_config": "nxos",
    "napalm": "nxos",
    "netmiko": "cisco_nxos",
    "netutils_parser": "cisco_nxos",
    "ntc_templates": "cisco_nxos",
    "pyats": "nxos",
    "pyntc": "cisco_nxos_nxapi",
    "scrapli": "cisco_nxos",
}
```

## _What are the supported platforms for Backup and Intended Configuration jobs? How do I configure a device with a specific OS?_

The current supported platform and the associated *default* platform network_driver names are the following for:

* arista_eos
* cisco_asa
* cisco_ios
* cisco_ios_xr
* cisco_nxos
* juniper_junos
* mikrotik_routeros
* mikrotik_routeros_api
* ruckus_fastiron
* ruckus_smartzone_api

In many use cases, this can be extended with a custom dispatcher for nornir tasks, which is controlled in the [nornir-nautobot](https://github.com/nautobot/nornir-nautobot) repository. Additionally you can "roll your own" dispatcher with the `custom_dispatcher` configuration parameter to map and/or extend for your environment. Please see the instructions there for further details.

## _Does this application provide the corrective configurations?_

Yes. While configuration enforcement is a challenging problem, this application integrates with [Hier Config](https://hier-config.readthedocs.io/en/latest/) to determine the commands required to bring a device into compliance with its intended configuration for traditional nested CLI config and allows you to bring your own custom remediation for JSON or XML based remediation.

## _Why does the compliance section scroll so much?_

The real estate optimizations is not the best for the configuration compliance overview right now. Users are suggested to review the best practices described in the configuration compliance section. Over time, the hope is to optimize this.

## _Why can't I get access to the name key when generating configuration?_

All data created by GraphQL is unpacked with the `**data` operator. There is a namespace issue with Nornir using name as a keyword as well. The recommended approach is to use GraphQL aliasing. An example would be `hostname: name` or `inventory_hostname: name` to workaround this issue.

## _It seems that Golden Config has caused an issue with migrations_

With the original Git Data Source implementation, passwords were stored in the database, encrypted with your `SECRET_KEY`. If you change your secret key, often the first migration that may cause an issue will be Golden Config, as shown here:

```bash
  Applying ipam.0006_ipaddress_nat_outside_list... OK
  Applying ipam.0007_add_natural_indexing... OK
  Applying nautobot_golden_config.0006_multi_repo_support_temp_field...Traceback (most recent call last):
  File "/usr/local/lib/python3.13/site-packages/django/db/models/fields/related_descriptors.py", line 173, in __get__
    rel_obj = self.field.get_cached_value(instance)
  File "/usr/local/lib/python3.13/site-packages/django/db/models/fields/mixins.py", line 15, in get_cached_value
    return instance._state.fields_cache[cache_name]
KeyError: 'backup_repository'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
<omitted>
  File "/usr/local/lib/python3.13/site-packages/cryptography/hazmat/backends/openssl/hmac.py", line 85, in verify
    raise InvalidSignature("Signature did not match digest.")
cryptography.exceptions.InvalidSignature: Signature did not match digest.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
<omitted>
  File "/usr/local/lib/python3.13/site-packages/django_cryptography/core/signing.py", line 239, in unsign
    raise BadSignature(
django.core.signing.BadSignature: Signature "b'A9QMEEeCk2+tAc6naf2KDiZBvACNWGNHGMPJ/SHOYY8=\n'" does not match
ERROR: 1
```

If you receive this error, the issue is the secret key has been changed, and **does not** have anything to do with the Golden Config app. You can either delete the entries from your data source and the reference to those in the Golden Config settings or revert the secret key back so it matches the original deployment. Any issues opened will be closed and this faq referred to. If you still need help, feel free to join the Slack community.

## _I got a `preemptively failed` error, but I know my system is setup correctly?_

These errors have been accurate so far, that is not to say that there is no way they could be a bug, but most commonly they have worked as expected thus far. Common issues include.

* Incorrectly configured Secrets
* Filtering to nothing when presumption is the filter works a certain way
* Referencing an OS that is not recognized

There is an ongoing effort to better document each [troubleshooting case](../admin/troubleshooting/index.md).

## _Why is the `_isnull` on DateTime filters considered experimental?_

There are various ways we can create a programmatic interface, which may change the behavior or name, for now it should be considered experimental as we may update this strategy.

## _I received an error `AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.` what should I do?_

Due to an incompatiblitly between DeepDiff and numPy, you must find a version of those two that are compatible with each other. See [here](https://github.com/seperman/deepdiff/issues/464) for more information. The easiest thing to do is upgrade them both.
