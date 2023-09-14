# App Overview

This document provides an overview of the App including critical information and import considerations when applying it to your Nautobot environment.

!!! note
    Throughout this documentation, the terms "app" and "plugin" will be used interchangeably.

## Description

When engineers are starting their network automation journey, everybody asks where and how they should start. Their immediate thought is coming up with methods of automating changes within their environments. However, doing so can be scary for those who are risk averse about automation making changes. The question then comes about how automation can be used to help solve some of the big problems facing network teams today. One of those problems that we’ve repeatedly heard from our customers and fellow network engineers is around configuration drift. This issue typically occurs for multiple reasons:

- Lack of standardization for device configurations
- Multiple individuals independently making changes
- Mergers and acquisitions

Thankfully, this issue can be addressed without making any changes on your devices. You might ask, “How do I do that?” That is where the Golden Configuration plugin for Nautobot comes in. The Golden Configuration plugin is comprised of four components:

- Configuration Backup
- Source of Truth Aggregation
- Configuration Intended
- Configuration Compliance

!!! info
    The four components are not hard requirements, the application is flexible and can be updated to leverage any of these components if they already exist in another system or automated process.

Utilizing these components, you can define the Golden Configuration standard for each of your devices and compare their adherence to that standard, otherwise known as their configuration compliance.

## Audience (User Personas) - Who should use this App?

- Network Engineers interested in Network Automation, Infrastructure as Code, etc.
- Network shops that have difficult time ensuring their configurations are to standard
- Network shops looking for a backup configuration solution
- Network shops looking for generating configurations

## Authors and Maintainers

- Ken Celenza (@itdependsnetworks)
- Jeff Kala (@jeffkala)

## Nautobot Features Used

!!! warning "Developer Note - Remove Me!"
    What is shown today in the Installed Plugins page in Nautobot. What parts of Nautobot does it interact with, what does it add etc. ?

### Extras

!!! warning "Developer Note - Remove Me!"
    Custom Fields - things like which CFs are created by this app?
    Jobs - are jobs, if so, which ones, installed by this app?
