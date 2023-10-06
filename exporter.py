import requests
from prometheus_client import CollectorRegistry, Gauge, start_http_server, Info
from requests.auth import HTTPBasicAuth
from time import sleep
import datetime
import time
import yaml


with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

url = config['url']
user = config['user']
password = config['password']
token = config['token']
token_creation = config['token_creation']
scrape_frequency = int(config['scrape_frequency'])
headers = {'x-zerto-session': token}

# Create new registry for metrics
registry = CollectorRegistry()

# VPG Metrics Gauges and Help strings
vpg_vms_count_help = 'Number of VMs in VPG'
vpg_vms_count = Gauge('vpg_vms_count', vpg_vms_count_help, ['vpg_name'], registry=registry)
vpg_used_storage_help = 'Used storage in MB'
vpg_used_storage = Gauge('vpg_used_storage', vpg_used_storage_help, ['vpg_name'], registry=registry)
vpg_iops_help = 'Number of IOPs'
vpg_iops = Gauge('vpg_iops', vpg_iops_help, ['vpg_name'], registry=registry)
vpg_throughput_help = 'Throughput in MB'
vpg_throughput = Gauge('vpg_throughput', vpg_throughput_help, ['vpg_name'], registry=registry)
vpg_actual_rpo_help = 'Actual RPO'
vpg_actual_rpo = Gauge('vpg_actual_rpo', vpg_actual_rpo_help, ['vpg_name'], registry=registry)
vpg_provisioned_storage_help = 'Provisioned Storage in MB'
vpg_provisioned_storage = Gauge('vpg_provisioned_storage', vpg_provisioned_storage_help, ['vpg_name'], registry=registry)
vpg_configured_rpo_help = 'Configured RPO'
vpg_configured_rpo = Gauge('vpg_configured_rpo', vpg_configured_rpo_help, ['vpg_name'], registry=registry)
vpg_last_test_help = 'Date of last test, in unix time'
vpg_last_test = Gauge('vpg_last_test', vpg_last_test_help, ['vpg_name'], registry=registry)
vpg_type_help = 'Possible values are: 0 or VCVpg | 2 or VCDvApp |4 or HyperV'
vpg_type = Gauge('vpg_type', vpg_type_help, ['vpg_name', 'type'], registry=registry)
vpg_status_help = 'VPG status (0 for "Initializing", 1 for "Meeting SLA", 2 for "Not Meeting SLA", 3 for "RPO Not Meeting SLA", 4 for "History Not Meeting SLA", 5 for "Failing Over", 6 for "Moving", 7 for "Deleting", 8 for "Recovered")'
vpg_status = Gauge('vpg_status', vpg_status_help, ['vpg_name'], registry=registry)
vpg_substatus_help = 'The substatus of the VPG, for example the VPG is in a bitmap sync'
vpg_substatus = Gauge('vpg_substatus', vpg_substatus_help, ['vpg_name'], registry=registry)
vpg_alert_status_help = 'Status of Alerts'
vpg_alert_status = Gauge('vpg_alert_status', vpg_alert_status_help, ['vpg_name'], registry=registry)
vpg_priority_help = 'The VPG priority (0 for "Low", 1 for "Medium", 2 for "High") Related endpoint: /v1/vpgs/priorities'
vpg_priority = Gauge('vpg_priority', vpg_priority_help, ['vpg_name'], registry=registry)

# Peersite Metrics Gauges and Help strings
peersite_pairing_status_help = 'The connection status of the peersite (0 for "Paired", 1 for "Pairing", 2 for "Unpaired")'
peersite_pairing_status = Gauge('peersite_pairing_status', peersite_pairing_status_help, ['peersite_name'], registry=registry)
peersite_location_help = 'The site location of the peer site defined during the installation or in the Site Information dialog'
peersite_location = Gauge('peersite_location', peersite_location_help, ['peersite_name', 'location'], registry=registry)
peersite_hostname_help = 'The address of a machine where a peer site Zerto Virtual Manager runs'
peersite_hostname = Gauge('peersite_hostname', peersite_hostname_help, ['peersite_name', 'hostname'], registry=registry)
peersite_port_help = 'The port used for communication by the Zerto Virtual Managers. The default port is 9669'
peersite_port = Gauge('peersite_port', peersite_port_help, ['peersite_name'], registry=registry)
peersite_provisioned_storage_help = 'The storage provisioned for all of the virtual machines in all the VPGs recovered to this site'
peersite_provisioned_storage = Gauge('peersite_provisioned_storage', peersite_provisioned_storage_help, ['peersite_name'], registry=registry)
peersite_used_storage_help = 'The storage used by all of the virtual machines in all the VPGs recovered to this site'
peersite_used_storage = Gauge('peersite_used_storage', peersite_used_storage_help, ['peersite_name'], registry=registry)
peersite_incoming_throughput_help = 'The Mb/s for all the applications running on the virtual machines being recovered on the peer site'
peersite_incoming_throughput = Gauge('peersite_incoming_throughput', peersite_incoming_throughput_help, ['peersite_name'], registry=registry)
peersite_outgoing_bandwidth_help = 'The bandwidth throttling defined for the site'
peersite_outgoing_bandwidth = Gauge('peersite_outgoing_bandwidth', peersite_outgoing_bandwidth_help, ['peersite_name'], registry=registry)
peersite_version_help = 'The Zerto Virtual Manager version'
peersite_version = Gauge('peersite_version', peersite_version_help, ['peersite_name', 'version'], registry=registry)
peersite_type_help = 'Possible values are: 0 or VCVpg | 2 or VCDvApp |4 or HyperV'
peersite_type = Gauge('peersite_type', peersite_type_help, ['peersite_name', 'type'], registry=registry)

# VM Metric Gauges and Help strings
vm_last_test_help = 'The date the last failover test occurred, in unix time'
vm_last_test = Gauge('vm_last_test', vm_last_test_help, ['vm_name', 'vpg_name'], registry=registry)
vm_priority_help = 'The priority specified for the VPG (0 for "Low", 1 for "Medium", 2 for "High")'
vm_priority = Gauge('vm_priority', vm_priority_help, ['vm_name', 'vpg_name'], registry=registry)
vm_provisioned_storage_help = 'The storage provisioned for the virtual machine in the recovery site.'
vm_provisioned_storage = Gauge('vm_provisioned_storage', vm_provisioned_storage_help, ['vm_name', 'vpg_name'], registry=registry)
vm_used_storage_help = 'The storage used by the virtual machine at the recovery site.'
vm_used_storage = Gauge('vm_used_storage', vm_used_storage_help, ['vm_name', 'vpg_name'], registry=registry)
vm_journal_used_storage_help = 'The amount of used journal storage for the virtual machine, in Mb'
vm_journal_used_storage = Gauge('vm_journal_used_storage', vm_journal_used_storage_help, ['vm_name', 'vpg_name'], registry=registry)
vm_journal_warning_threshold_limit_type_help = 'The type of Journal size limit (0 for Unlimited, 1 or Megabytes, 2 for Percentage)'
vm_journal_warning_threshold_limit_type = Gauge('vm_journal_warning_threshold_limit_type', vm_journal_warning_threshold_limit_type_help, ['vm_name', 'vpg_name'], registry=registry)
vm_journal_warning_threshold_limit_value_help = 'The journal size that generates a warning that the journal is nearing its hard limit'
vm_journal_warning_threshold_limit_value = Gauge('vm_journal_warning_threshold_limit_value', vm_journal_warning_threshold_limit_value_help, ['vm_name', 'vpg_name'], registry=registry)
vm_iops_help = 'The IO per second between all the applications running on the virtual machine in the VPG and the VRA that sends a copy to the remote site for replication'
vm_iops = Gauge('vm_iops', vm_iops_help, ['vm_name', 'vpg_name'], registry=registry)
vm_throughput_help = 'The MBs for all the applications running on the virtual machine being protected.'
vm_throughput = Gauge('vm_throughput', vm_throughput_help, ['vm_name', 'vpg_name'], registry=registry)
vm_outgoing_bandwidth_help = 'The bandwidth throttling defined for the virtual machines.'
vm_outgoing_bandwidth = Gauge('vm_outgoing_bandwidth', vm_outgoing_bandwidth_help, ['vm_name', 'vpg_name'], registry=registry)
vm_actual_rpo_help = 'The time since the last checkpoint was written to the journal in seconds. This should be less than the Target RPO Alert value specified for the VPG. A value of -1 means that the RPO has not been calculated.'
vm_actual_rpo = Gauge('vm_actual_rpo', vm_actual_rpo_help, ['vm_name', 'vpg_name'], registry=registry)
vm_volumes_help = 'The identifier of the volume used by the virtual machine. The volume identifier uses the SCSI standard to describe controllers and units, for example: SCSI:0:0.'
vm_volumes = Gauge('vm_volumes', vm_volumes_help, ['vm_name', 'vpg_name', 'volumes'], registry=registry)
vm_status_help = ' The status of the VPG that contains the virtual machine. Possible values: (0 for "Initializing", 1 for "Meeting SLA", 2 for "Not Meeting SLA", 3 for "RPO Not Meeting SLA", 4 for "History Not Meeting SLA", 5 for "Failing Over", 6 for "Moving", 7 for "Deleting", 8 for "Recovered")'
vm_status = Gauge('vm_status', vm_status_help, ['vm_name', 'vpg_name'], registry=registry)
vm_substatus_help = 'The substatus of the VPG that contains the virtual machine, for example the VPG is in a bitmap sync. For the description of substatuses, refer to the Zerto Virtual Manager Administration Guide'
vm_substatus = Gauge('vm_substatus', vm_substatus_help, ['vm_name', 'vpg_name'], registry=registry)
vm_exists_help = '1 - True: The VM exists. 2 - False: The VM does not exist.'
vm_exists = Gauge('vm_exists', vm_exists_help, ['vm_name', 'vpg_name' , "exists"], registry=registry)
vm_enabled_actions_is_flr_enabled_help = 'Whether file level restore is enabled'
vm_enabled_actions_is_flr_enabled = Gauge('vm_enabled_actions_is_flr_enabled', vm_enabled_actions_is_flr_enabled_help, ['vm_name', 'vpg_name', 'enabled_actions_is_flr_enabled'], registry=registry)
vm_hardware_version_help = 'The VMware hardware version. '
vm_hardware_version = Gauge('vm_hardware_version', vm_hardware_version_help, ['vm_name', 'vpg_name', 'hardware_version'], registry=registry)

# function that loads creds from config.yaml and tries current token. generates new one if that fails
def GetAuth():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    url = config['url']
    user = config['user']
    password = config['password']
    token = config['token']
    token_creation = config['token_creation']
    headers = {'x-zerto-session': token}
    retries = 0
    delay = 0
    # if the token works, we're good
    response = requests.get(url + "/localsite", headers=headers, verify=False)
    if response.status_code == 200:
        print("Successfully authenticated")
        sleep(5)
    # if the token returns 401 we need a new token
    elif response.status_code == 401:
        print("Unauthorized request... requesting new session")
        try:
            response = requests.post(url + "/session/add", auth=HTTPBasicAuth(user, password), verify=False)
            token = response.headers.get("x-zerto-session")
            token_creation = response.headers.get("Date")
            config['token'] = token
            config['token_creation'] = token_creation
            headers = {'x-zerto-session': token}
            # write token string to config.yaml file
            with open ('config.yaml', 'w') as f:
                yaml.dump(config, f)
            retries += 1
            delay = 2 ** retries
            sleep(delay)
        except requests.exceptions.HTTPError as http_err: # catches HTTP errors like 404 Not Found, 500 internal server error
            print(f"HTTP error occurred: {http_err}")
            retries += 1
            delay = 2 ** retries
            sleep(delay)
        except requests.exceptions.RequestException as req_err: # catches other types of exceptions
            print(f"Request error occurred: {req_err}")
            retries += 1
            delay = 2 ** retries
            sleep(delay)
    elif response.status_code != 200:
        print("ERROR?!") 
    sleep(5)

# function that gets metrics about Virtual Protection Groups (VPGs)
def GetVpgStatsFunc():
    response = requests.get(url + "/vpgs", headers=headers, verify=False)
    json_data = response.json()

    for vpg in json_data:
        vpg_name = vpg.get('VpgName')
        vms_count = vpg.get('VmsCount')
        vpg_vms_count.labels(vpg_name=vpg_name).set(vms_count)
        used_storage = vpg.get('UsedStorageInMB')
        vpg_used_storage.labels(vpg_name=vpg_name).set(used_storage)
        iops = vpg.get('IOPs')
        vpg_iops.labels(vpg_name=vpg_name).set(iops)
        throughput = vpg.get('ThroughputInMB')
        vpg_throughput.labels(vpg_name=vpg_name).set(throughput)
        actual_rpo = vpg.get('ActualRPO')
        vpg_actual_rpo.labels(vpg_name=vpg_name).set(actual_rpo)
        provisioned_storage = vpg.get('ProvisionedStorageInMB')
        vpg_provisioned_storage.labels(vpg_name=vpg_name).set(provisioned_storage)
        configured_rpo = vpg.get('ConfiguredRpoSeconds')
        vpg_configured_rpo.labels(vpg_name=vpg_name).set(configured_rpo)
        last_test_string = vpg.get('LastTest')
        last_test = datetime.datetime.fromisoformat(last_test_string[:-1]).timestamp() # convert to unix timestamp
        vpg_last_test.labels(vpg_name=vpg_name).set(last_test)
        type = vpg.get('VpgType')
        vpg_type.labels(vpg_name=vpg_name, type=type).set(1)
        status = vpg.get('Status')
        vpg_status.labels(vpg_name=vpg_name).set(status)
        substatus = vpg.get('SubStatus')
        vpg_substatus.labels(vpg_name=vpg_name).set(substatus)
        # need to add ActiveProcessesApi.RunningFailOverTestApi
        alert_status = vpg.get('AlertStatus')
        vpg_alert_status.labels(vpg_name=vpg_name).set(alert_status)
        priority = vpg.get('Priority')
        vpg_priority.labels(vpg_name=vpg_name).set(priority)

# function that gets metrics about Peer Sites 
def GetSiteStatsFunc():
    response = requests.get(url + "/peersites", headers=headers, verify=False)
    json_data = response.json()

    for peersite in json_data:
        peersite_identifier = peersite.get('SiteIdentifier')
        peersite_name = peersite.get('PeerSiteName')
        pairing_status = peersite.get('PairingStatus')
        peersite_pairing_status.labels(peersite_name=peersite_name).set(pairing_status)
        location = peersite.get('Location')
        peersite_location.labels(peersite_name=peersite_name, location=location).set(1)
        hostname = peersite.get('HostName')
        peersite_hostname.labels(peersite_name=peersite_name, hostname=hostname).set(1)
        port = peersite.get('Port')
        peersite_port.labels(peersite_name=peersite_name).set(port)
        provisioned_storage = peersite.get('ProvisionedStorage')
        peersite_provisioned_storage.labels(peersite_name=peersite_name).set(provisioned_storage)
        used_storage = peersite.get('UsedStorage')
        peersite_used_storage.labels(peersite_name=peersite_name).set(used_storage)
        incoming_throughput = peersite.get('IncomingThroughputInMb')
        peersite_incoming_throughput.labels(peersite_name=peersite_name).set(incoming_throughput)
        outgoing_bandwidth = peersite.get('OutgoingBandWidth')
        peersite_outgoing_bandwidth.labels(peersite_name=peersite_name).set(outgoing_bandwidth)
        version = peersite.get('Version')
        peersite_version.labels(peersite_name=peersite_name, version=version).set(1)
        type = peersite.get('SiteType')
        peersite_type.labels(peersite_name=peersite_name, type=type).set(1)

# function that gets metrics about Virtual Machines (VMs)
def GetVMStatsFunc():
    response = requests.get(url + "/vms", headers=headers, verify=False)
    json_data = response.json()

    for vm in json_data:
        vm_name = vm.get('VmName')
        vm_identifier = vm.get('VmIdentifier')
        vpg_name = vm.get('VpgName')
        organization_name = vm.get('OrganizationName')
        priority = vm.get('Priority')
        vm_priority.labels(vm_name=vm_name, vpg_name=vpg_name,).set(priority)
        provisioned_storage = vm.get('ProvisionedStorageInMB')
        vm_provisioned_storage.labels(vm_name=vm_name, vpg_name=vpg_name,).set(provisioned_storage)
        used_storage = vm.get('UsedStorageInMB')
        vm_used_storage.labels(vm_name=vm_name, vpg_name=vpg_name,).set(used_storage)
        journal_used_storage = vm.get('JournalUsedStorageMb')
        vm_journal_used_storage.labels(vm_name=vm_name, vpg_name=vpg_name,).set(journal_used_storage)
        journal_warning_threshold_limit_type = vm.get('JournalHardLimit').get("LimitType")
        vm_journal_warning_threshold_limit_type.labels(vm_name=vm_name, vpg_name=vpg_name,).set(journal_warning_threshold_limit_type)
        journal_warning_threshold_limit_value = vm.get('JournalHardLimit').get("LimitValue")
        vm_journal_warning_threshold_limit_value.labels(vm_name=vm_name, vpg_name=vpg_name,).set(journal_warning_threshold_limit_value)
        iops = vm.get('IOPs')
        vm_iops.labels(vm_name=vm_name, vpg_name=vpg_name,).set(iops)
        throughput = vm.get('ThroughputInMB')
        vm_throughput.labels(vm_name=vm_name, vpg_name=vpg_name,).set(throughput)
        outgoing_bandwidth = vm.get('OutgoingBandWidthInMbps')
        vm_outgoing_bandwidth.labels(vm_name=vm_name, vpg_name=vpg_name,).set(outgoing_bandwidth)
        actual_rpo = vm.get('ActualRPO')
        vm_actual_rpo.labels(vm_name=vm_name, vpg_name=vpg_name,).set(actual_rpo)
        last_test_string = vm.get('LastTest')
        last_test = datetime.datetime.fromisoformat(last_test_string[:-1]).timestamp() # convert to unix timestamp
        vm_last_test.labels(vm_name=vm_name, vpg_name=vpg_name).set(last_test)
        volumes = vm.get('Volumes')[0].get('VmVolumeIdentifier')
        vm_volumes.labels(vm_name=vm_name, vpg_name=vpg_name, volumes=volumes).set(1)
        status = vm.get('Status')
        vm_status.labels(vm_name=vm_name, vpg_name=vpg_name,).set(status)
        substatus = vm.get('SubStatus')
        vm_substatus.labels(vm_name=vm_name, vpg_name=vpg_name,).set(substatus)
        enabled_actions_is_flr_enabled = vm.get('EnabledActions').get('IsFlrEnabled')
        vm_enabled_actions_is_flr_enabled.labels(vm_name=vm_name, vpg_name=vpg_name, enabled_actions_is_flr_enabled=enabled_actions_is_flr_enabled).set(1)
        exists = vm.get('IsVmExists')
        if exists == "true":
            vm_exists.labels(vm_name=vm_name, vpg_name=vpg_name, exists=exists).set(1)
        elif exists == "false":
            vm_exists.labels(vm_name=vm_name, vpg_name=vpg_name, exists=exists).set(2)
        hardware_version = vm.get('HardwareVersion')
        vm_hardware_version.labels(vm_name=vm_name, vpg_name=vpg_name, hardware_version=hardware_version).set(1)


# first perform auth, create new token if necessary
GetAuth()

# after auth function runs, loads creds from config.yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

token = config['token']
token_creation = config['token_creation']
headers = {'x-zerto-session': token}

# Start HTTP server to expose Prometheus metrics
start_http_server(8080, registry=registry)

# Scrape the Zerto API every {scrape_frequency} seconds and publ
while True:
    GetVpgStatsFunc()
    GetSiteStatsFunc()
    GetVMStatsFunc()
    time.sleep(scrape_frequency)
