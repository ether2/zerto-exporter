# zerto-exporter
Prometheus exporter, using the Python Prometheus Client library - for Zerto Virtual Manager.

Tested on ZVM version 9.5+ running on Windows server.

This exporter authenticates with ZVM, generating a session token if necessary. Then calls ZVM API to generate metrics on peer sites, vpgs and vms.

Then runs an http server exposing Prometheus metrics at http://localhost:8080/metrics.

Metrics include:

vpg_
vm_
peersite_
