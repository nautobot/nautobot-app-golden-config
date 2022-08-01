# App Overview

The golden configuration plugin is a Nautobot plugin that aims to solve common configuration management challenges.

## Description/Overview

When engineers are starting their network automation journey, everybody asks where and how they should start. Their immediate thought is coming up with methods of automating changes within their environments. However, doing so can be scary for those who are risk averse about automation making changes. The question then comes about how automation can be used to help solve some of the big problems facing network teams today. One of those problems that we’ve repeatedly heard from our customers and fellow network engineers is around configuration drift. This issue typically occurs for multiple reasons:

- Lack of standardization for device configurations
- Multiple individuals independently making changes
- Mergers and acquisitions

Thankfully, this issue can be addressed without making any changes on your devices. You might ask, “How do I do that?” That is where the Golden Configuration plugin for Nautobot comes in. The Golden Configuration plugin is comprised of four components:

- Configuration Backup
- Source of Truth Aggregation
- Configuration Intended
- Configuration Compliance

Utilizing these components, you can define the Golden Configuration standard for each of your devices and compare their adherence to that standard, otherwise known as their configuration compliance.

## Audience (User Personas) - Who should use this App?

- Network Engineers interested in Network Automation, Infrastructure as Code, etc.
- Network shops that have difficult time ensuring their configurations are to standard
- Network shops looking for a backup configuration solution
- Network shops looking for generating configurations

## Authors and Maintainers

- Ken Celenza (@itdependsnetworks)
- Jeff Kala (@jeffkala)
