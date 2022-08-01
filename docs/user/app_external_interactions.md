# External Interactions

### From the App to Other Systems

- Git integrations are required, this is generally tcp/22 or tcp/443 to the git repository.
    - An account with priveleges to read and/or write (depending on features used) with git
- When using backup configurations, will require access to the port of the network device, usually tcp/22 or tcp/443.
    - An account with priveleges to read configurations

## Nautobot REST API endpoints

- Documentation of the API is provided by OpenAPI (formerly Swagger) docs.