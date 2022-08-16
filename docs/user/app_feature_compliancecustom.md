# Navigating Compliance With Custom Logic

## Caveats

- The compliance `rule` must be unique for the Custom `config-type`.
- The data provided can come from either setting via the API like JSON or via match_config like CLI. It is up to the operator to enforce.
- Does not make any accommodations for adding to git.
- Mixing/Matching string (or CLI type) and JSON type compliance rules is **NOT** supported. A device should only have compliance rules from one or the other, and it is up to the operator to enforce.
    - Applying a `match_config` presumes it is CLI type and not having one presumes it is JSON type.
- If the developer of the `get_custom_compliance` is not cognizant, the UI experience of the details may not always be obvious what the issues are.
    - As an example, if the developer simply returns a `True` or `False` into the missing or extra dictionary, it will not be obvious to the user.
- The developer is responsible for ensuring the proper data structure is maintained for the given rule.

## Justification

While the maintainers believe that the proper way to provide configuration compliance is the opinionated solutions provided, which compares intended
state vs actual state, we are conscious that this may not always be a viable solution for all organizations. As an example, complicated configurations may not be ready for intended state, but there are still several parts of the configuration you will need to ensure always exists, such as "making sure all BGP peers have authentication configured."

Providing additional opinionated solutions is both not in-line with the intention of the project nor is it feasible to provide a solution that will work for many people. For those reasons, it was decided to create an extendible interface for developers/operators to create their custom compliance logic.

Finally, it is understood that one of the key values provided by the Golden Config plugin is the visualization of the compliance and quick access to the tooling. Providing the interface to `get_custom_compliance` function allows the developers/operators the ability to get their own compliance process integrated with the user experience provided by the plugin.

## The Interface

The interface of contract provided to your custom function is based on the following:

### Inputs

- The function is called with a single parameter called `obj`, so your function must be set to accept `obj` as a kwarg.
- The `obj` parameter, is the `self` instance object of a `ConfigCompliance` model, review the documentation for the all attributes of a `ConfigCompliance` instance, but the common ones are documented below.
    - `obj.actual` - The **actual** configuration parsed out by the `match_config` logic, or what was sent via the API.
    - `obj.intended` - The **intended** configuration parsed out by the `match_config` logic, or what was sent via the API.
    - `obj.device.platform.slug` -  The platform slug name.
    - `obj.rule.config_ordered` - describes whether or not the rule was configured to be ordered, such as an ACL, or not such as SNMP servers
    - `obj.rule` - The name of the rule.
    - `obj.rule.match_config` - The match_config text the rule was configured with.

### Outputs

- The function should return a single dictionary, with the keys of `compliance`, `compliance_int`, `ordered`, `missing`, and `extra`.
- The `compliance` key should be a boolean with either True or False as acceptable responses, which determines if the config is compliant or not.
- The `compliance_int` key should be an integer with either 1 (when compliance is True) or 0 (when compliance is False) as acceptable responses. This is required to handle a counting use case where boolean does not suffice.
- The `ordered` key should be a boolean with either True or False as acceptable responses, which determines if the config is compliant and ordered or not.
- The `missing` key should be a string or json, empty when nothing is missing and appropriate string or json data when configuration is missing.
- The `extra` key should be a string or json, empty when nothing is extra and appropriate string or json data when there is extra configuration.

There is validation to ensure the data structure returned is compliant to the above assertions.

The function provided in string path format, must be installed in the same environment as nautobot and the workers.

## Configuration

The path to the function is set in the `get_custom_compliance` configuration parameter. This is the string representation of the function and must be in
Python importable into Nautobot and the workers. This is a callable function and not a class or other object type.

```python
PLUGINS_CONFIG = {
    "nautobot_golden_config": {
        "get_custom_compliance": "my.custom_compliance.custom_compliance_func"
    }
}
```

## Example

To provide boiler plate code for any future use case, the following is provided

```python
def custom_compliance_func(obj):
    # Modify with actual logic, this would always presume compliant.
    compliance_int = 1
    compliance = True
    ordered = True
    missing = ""
    extra = ""
    return {
        "compliance": compliance,
        "compliance_int": compliance_int,
        "ordered": ordered,
        "missing": missing,
        "extra": extra,
    }
```

Below is an actual example, it takes a very direct approach for matching platform and rule type to a check. This can naturally be modified to apply the abstract logic one may wish to provide.

```python
# expected_actual_config = '''router bgp 400
#  no synchronization
#  bgp log-neighbor-changes
#  neighbor 70.70.70.70 remote-as 400
#  neighbor 70.70.70.70 password cisco
#  neighbor 70.70.70.70 update-source Loopback80
#  no auto-summary
# '''
import re
BGP_PATTERN = re.compile("\s*neighbor (?P<ip>\d+\.\d+\.\d+\.\d+) .*")
BGP_SECRET = re.compile("\s*neighbor (?P<ip>\d+\.\d+\.\d+\.\d+) password (\S+).*")
def custom_compliance_func(obj):
    if obj.rule == 'bgp' and obj.device.platform.slug == 'ios':
        actual_config = obj.actual
        neighbors = []
        secrets = []
        for line in actual_config.splitlines():
            match = BGP_PATTERN.search(line)
            if match:
                neighbors.append(match.groups("ip")[0])
            secret_match = BGP_SECRET.search(line)
            if secret_match:
                secrets.append(match.groups("ip")[0])
    neighbors = list(set(neighbors))
    secrets = list(set(secrets))
    if secrets != neighbors:
        compliance_int = 0
        compliance = False
        ordered = False
        missing = f"neighbors Found: {str(neighbors)}\nneigbors with secrets found: {str(secrets)}"
        extra = ""
    else:
        compliance_int = 1
        compliance = True
        ordered = True
        missing = ""
        extra = ""
    return {
        "compliance": compliance,
        "compliance_int": compliance_int,
        "ordered": ordered,
        "missing": missing,
        "extra": extra,
    }
```

In the above example, one may observe that there is no reference to `obj.intended`, that is because this logic is not concerned about such information.

As the developer of such solutions, you may not require intended configuration or other attributes, but be conscious on the user experience implications. It may seem odd to some users to have blank intended configuration but compliance set to true as an example or it may seem odd to have instructions for fixes rather than configurations.
