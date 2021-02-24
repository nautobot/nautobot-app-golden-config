
# Usage

There is a single process and several views that the plugin provides.

## Plugins Buttons

The plugins buttons provides you the ability to navigate to Run the script, overview report, and detailed report.


## Run Script

This can be accessed via the Plugins drop-down via `Run Script` button, it will immediately run the script once the it starts.


## Detail Report

This can be accessed via the Plugins drop-down via `Compliance` details button. From there you can filter the devices via the form on the right side, limit the columns with the `Configure` button, or 
bulk delete with the `Delete` button. Additionally each device is click-able to view the details of that individual device. 

You can configure the columns to limit how much is showing on one screen.

## Device Details

You can get to the device details form either the Compliance details page, or there is a `content_template` on the device model page is Nautobot's core instance (more details later.)


## Overview Report

There is a global overview or executive summary that provides a high level snapshot of the compliance. There are 3 points of data captured.

* Devices - This is only compliant if there is not a single non-compliant feature on the device. So if there is 10 features, and 1 feature is not compliant, the device is considered non-compliant.
* Features - This is the total number of features for all devices, and how many are compliant, and how many are non-compliant.
* Per Feature - This is a breakdown of that feature and how many within that feature are compliant of not.

## Device Template Content

The plugin makes use of template content `right_page` in order to use display in-line the status of that device in the traditional Nautobot view. From here you can click the link to see the
detail compliance view.


## Site Template Content

The plugin makes use of template content `right_page` in order to use display in-line the status of that entire site in the traditional Nautobot view. 
