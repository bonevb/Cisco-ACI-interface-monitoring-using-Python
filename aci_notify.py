import requests
import json
from aci_login import get_token
from datetime import datetime
from smtplib import SMTP
from email.mime.text import MIMEText
from time import sleep
import re

def send_email(subject, body, toaddr="intranet@dux.bg"):
    fromaddr = "aci_fauts@dux.bg"
    msg = MIMEText(body, 'plain')
    msg['To'] = toaddr
    msg['Subject'] = subject

    server = SMTP('smtp.dux.bg', 25)
    # server.login(fromaddr, "y0ur_p4ssw0rd")
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()



def calculate_time_diff(d):
    # d = '2021-03-23T13:07:05.500+02:00'
    date = d.split('T')
    # print(date[0])
    # print(date[1].split('+')[0].split('.')[0])
    cur_date = date[0] + " " + date[1].split('+')[0].split('.')[0]
    # print(cur_date)

    result = datetime.strptime(cur_date, "%Y-%m-%d %H:%M:%S")

    today = datetime.now()
    differ = today - result
    duration = differ.total_seconds() / 60
    return duration

urls = [
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1201/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1202/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1203/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1204/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1205/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1206/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1207/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1208/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1209/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1210/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1101/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-1/node-1102/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-2/node-2201/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-2/node-2202/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-2/node-2203/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-2/node-2204/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-2/node-2101/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")',
             'https://10.10.10.10/api/node/class/topology/pod-2/node-2102/faultRecord.json?query-target-filter=eq(faultRecord.code,"F0532")'
             ]

token = get_token()

def get_tenants(url):
#    token = get_token()

    headers = {
        "Cookie": f"APIC-Cookie={token}",
    }

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=headers, verify=False)

    return response


if __name__ == "__main__":
    for url in urls:
        response = get_tenants(url).json()
        tenants = response['imdata']

        for tenant in tenants:
            # print(tenant['faultRecord'])
            if 'faultRecord' in tenant.keys():
                if tenant['faultRecord']['attributes']['severity'] == 'cleared': #and tenant['faultRecord']['attributes']['prevSeverity'] == 'critical':
                    date = tenant['faultRecord']['attributes']['created']
                    decidion = calculate_time_diff(date)
                    # print(decidion)
                    if decidion < 5:
                         temp = tenant['faultRecord']['attributes']['affected']
                         a, _ = temp.split(']')
                         topology = a + ']'
                         url1 = 'https://sdn.ad.btk.bg/api/node/mo/' + topology + '.json'
                         desc = get_tenants(url1).json()
                         desc1 = desc['imdata']

                         if 'l1PhysIf' in desc1[0]:
                             port_desc = 'Interface description: ', (desc1[0]['l1PhysIf']['attributes']['pathSDescr']), '\n'
                         else:
                             port_desc = 'Interface description: ', 'No description' + '\n'
                         affected = 'Affected: ',tenant['faultRecord']['attributes']['affected']+ "\n"
                         cause = 'Cause: ',tenant['faultRecord']['attributes']['cause']+ "\n"
                         description = 'Description: ',tenant['faultRecord']['attributes']['descr']+ "\n"
                         occur = 'Last occurance: ',tenant['faultRecord']['attributes']['created']+ "\n"
                         message = port_desc + affected + cause + description + occur
                         body = f"Fault is cleared :\n{''.join(message)}"
                         #print(body)
                         # print(port_desc)
                         if re.findall(r'po[0-9]+', tenant['faultRecord']['attributes']['affected']) == []:
                             if not 'RDCESX54' in desc1[0]['l1PhysIf']['attributes']['pathSDescr']:
                                 send_email('Clearing critical fault in Cisco ACI', body)
            #              print(tenant['faultRecord']['attributes'])
                     # print(tenant['faultDelegate']['attributes']['severity'])
                elif tenant['faultRecord']['attributes']['severity'] == 'critical'and tenant['faultRecord']['attributes']['lc'] == 'raised' or tenant['faultRecord']['attributes']['lc'] == 'soaking':
                    date = tenant['faultRecord']['attributes']['created']
                    decidion = calculate_time_diff(date)
                    # print(decidion)
                    if decidion < 5:
                        temp = tenant['faultRecord']['attributes']['affected']
                        a, _ = temp.split(']')
                        topology = a + ']'
                        url1 = 'https://sdn.ad.btk.bg/api/node/mo/' + topology + '.json'
                        desc = get_tenants(url1).json()
                        desc1 = desc['imdata']

                        if 'l1PhysIf' in desc1[0]:
                            port_desc = 'Interface description: ', (
                            desc1[0]['l1PhysIf']['attributes']['pathSDescr']), '\n'
                        else:
                            port_desc = 'Interface description: ', 'No description' + '\n'
                        affected = 'Affected: ', tenant['faultRecord']['attributes']['affected'] + "\n"
                        cause = 'Cause: ', tenant['faultRecord']['attributes']['cause'] + "\n"
                        description = 'Description: ', tenant['faultRecord']['attributes']['descr'] + "\n"
                        occur = 'Last occurance: ', tenant['faultRecord']['attributes']['created'] + "\n"
                        message = port_desc + affected + cause + description + occur
                        body = f"Fault is :\n{''.join(message)}"
                        #print(body)
                        if re.findall(r'po[0-9]+', tenant['faultRecord']['attributes']['affected']) == []:
                            if not 'RDCESX54' in desc1[0]['l1PhysIf']['attributes']['pathSDescr']:
                                send_email('New critical fault in Cisco ACI', body)


