# Configuration Hash Grouping

The **Configuration Hash Grouping** feature enables administrators to identify devices that have identical non-compliant configurations, making it easier to troubleshoot and fix configuration issues that affect multiple devices simultaneously. This feature groups devices by their configuration hash values, allowing you to see patterns in configuration drift and apply fixes to entire groups at once.

## Overview

When configuration compliance issues affect multiple devices with identical misconfigurations, the traditional approach of reviewing each device individually can be time-consuming and inefficient. The Configuration Hash Grouping feature solves this by:

- Automatically grouping devices with identical configuration hashes
- Providing a unified view of devices sharing the same configuration issues
- Enabling bulk remediation operations on groups of devices
- Simplifying troubleshooting of widespread configuration problems

## How It Works

The Configuration Hash Grouping feature uses a three-model architecture to efficiently organize and display configuration data:

### Architecture Components

1. **ConfigHashGrouping**: Groups devices with identical configuration hashes
2. **ConfigComplianceHash**: Links individual devices to configuration hash groups
3. **ConfigCompliance**: Provides the base compliance data (existing model, modified for integration)

### Hash Generation Process

When configuration compliance jobs run, the system:

1. Computes SHA-256 hashes of device configuration content
2. Creates or finds existing ConfigHashGrouping records for each unique hash
3. Links devices to the appropriate hash groups via ConfigComplianceHash records
4. Stores the actual configuration content once per unique hash for display purposes

This approach eliminates duplicate storage while maintaining fast access to configuration data for analysis.

## Accessing Configuration Hash Grouping

To access the Configuration Hash Grouping feature:

1. Navigate to **Golden Config** in the main navigation menu
2. Under the **Manage** section, select **Hash Grouping Report**
3. The main view displays groups of devices with identical configuration hashes

!!! note
    You must have the `view_configcompliance` permission to access this feature.

## Configuration Hash Grouping Views

### Main Grouping View

The main Configuration Hash Grouping view (`/config-compliance/hash-grouping/`) displays:

- **Feature Name**: The compliance rule feature being evaluated
- **Device Count**: Number of devices sharing the same configuration hash (clickable to view devices)
- **Configuration Preview**: Expandable view of the actual configuration content
- **Action Buttons**: Quick access to remediation jobs and other operations

### Device-Level Hash View

The device-level view (`/config-compliance/config-hash/`) provides:

- Individual device details linked to their hash groups
- Device-specific configuration information
- Direct navigation to device compliance details

### Interactive Features

The user interface includes several interactive elements:

- **Expand/Collapse**: Toggle individual configuration displays
- **Master Toggle**: Expand or collapse all configurations at once
- **AJAX Loading**: Smooth loading of configuration content without page refreshes
- **Fixed-Width Containers**: Consistent layout that prevents content shifting

## API Access

The Configuration Hash Grouping feature provides REST API access for programmatic integration:

### Endpoints

- **ConfigHashGrouping**: `/api/plugins/golden-config/config-hash-grouping/`
- **ConfigComplianceHash**: `/api/plugins/golden-config/config-compliance-hash/`

### Example API Usage

```bash
# Get all hash groups
curl -H "Authorization: Token YOUR_TOKEN" \
  http://nautobot/api/plugins/golden-config/config-hash-grouping/

# Get devices in a specific hash group
curl -H "Authorization: Token YOUR_TOKEN" \
  http://nautobot/api/plugins/golden-config/config-compliance-hash/
```

## Summary

The Configuration Hash Grouping feature represents a significant enhancement to Nautobot Golden Config's compliance capabilities. By grouping devices with identical configuration hashes, it provides network administrators with powerful tools for identifying, analyzing, and resolving configuration issues at scale. The feature's three-model architecture ensures excellent performance while maintaining data integrity, and its seamless integration with existing Golden Config functionality makes it immediately useful in any network automation workflow.
