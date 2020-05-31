#!/usr/bin/python
'''Backend Program
Developed from 15-Oct-2019 to **-***-****
'''

import time
from datetime import datetime
import sqlite3
from easysnmp import Session
from sqlite3 import Error

V_LAN = 'DEFAULT_VLAN(1)'
def establish_connection(db_file):
    """  establish a database connection to a SQLite database """
    connections = None
    try:
        connections = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    finally:
        if connections:
            data = connections.execute('Select * from manager')
            for items in data:
                ip = items[0]; port=int(items[1]); community=items[2]; version=int(items[3])
                probe_device(ip, port, community,version, connections)

            connections.close()
def probe_device(ip, port, community, version, connections):
    oids = {'dot1dTpFdbEntryAddress':'1.3.6.1.2.1.17.4.3.1.1',
            'dot1dTpFdbEntryPort':'1.3.6.1.2.1.17.4.3.1.2',
            'dot1qTpFdbEntryStatus':'1.3.6.1.2.1.17.4.3.1.3',
            'dot1qTpFdbAddress':'1.3.6.1.2.17.7.1.2.2.1.1',
            'dot1qTpFdbPort':'1.3.6.1.2.1.17.7.1.2.2.1.2',
            'dot1qTpFdbStatus':'1.3.6.1.2.1.17.7.1.2.2.1.3',
            'dot1qVlanStaticName':'1.3.6.1.2.1.17.7.1.4.3.1.1',
            'sysDescr':'1.1.3.6.1.2.1.1.1',
            'dot1dBasePortIfIndex':'1.3.6.1.2.1.17.1.4.1.2',
            'vlans':'1.3.6.1.2.1.17.7.1.4.3.1.4'}
    try:
        session = Session(hostname=ip, remote_port=port, version=version, community=community)
    except Exception as e:
        print(e)
        failed_attempts = connections.execute("select failed_attempts from manager where ip=?, port=?",(ip,port))
        failed_attempts += 1
        connections.execute("update manager set failed_attempts=? where (ip=? and port=?)",(failed_attempts,ip,port))
        connections.commit()
    start = str(datetime.fromtimestamp(int(time.time())))
    try:
        macs = session.walk(oids['dot1dTpFdbEntryAddress'])
        ports = session.walk(oids['dot1dTpFdbEntryPort'])
        for m,p in zip(macs, ports):
            oid = m.oid;oid_index = m.oid_index;snmp_type=m.snmp_type
            mac = ':'.join('{:02x}'.format(ord(a)) for a in m.value)
            portval = p.value
            data = connections.execute("SELECT * from finalproject where (PORT=? and IPADDRESS=?)",(portval,ip))
            fetch_data = data.fetchall()
            for connected_macs in fetch_data:
                m = connected_macs[3]
            if len(fetch_data)==0:
                connections.execute('''INSERT INTO finalproject(IPADDRESS, VLAN, PORT, MACS) values (?,?,?,?)''',(ip,VL,portval,mac))
                connections.commit()
            elif len(fetch_data)==1 and m.find(mac)==-1:
                finalmac = m+","+mac
                connections.execute("UPDATE finalproject set MACS=? where PORT=?",(finalmac,portval))
                connections.commit()
        vlansnum = []
        vlanname = []
        vlans = session.walk(oids['vlans'])
        vlanindex = session.walk(oids['dot1qVlanStaticName'])
        values = []
        vlan_oids = []
        for index, vlan in zip(vlanindex, vlans):
            value = ':'.join('{:02x}'.format(ord(x)) for x in vlan.value)
            values = value.split(':')
            oid = vlan.oid
            vlan_oids.append(oid)
            vname = index.value
            vnums = oid.split('.')
            vnum = str(vnums[-1])
            combine = ''
            if vname != V_LAN:
                for i in range(len(values)):
                    hexlist = values
                    mac_hex = hexlist[i]
                    scale = 16
                    no_of_bits = 8
                    orghex = bin(int(mac_hex, scale))[2:].zfill(no_of_bits)
                    combine = combine + str(orghex)
                    orghex = ''
                    listvls = list(combine)
                for i in range(len(listvls)):
                    if listvls[i] == '1':
                        num = i + 1
                        vlanname.append(str(vname) + '(' + vnum + ')')
                        vlansnum.append(num)
        for i in range(len(vlansnum)):
            portlan = '1'
            connections.execute("update finalproject set VLAN = ? where PORT=?", (vlanname[i],vlansnum[i]))
            connections.commit()
    except Exception as e:
        print(str(e)+' '+str(ip)+":"+str(port))
    finish = str(datetime.fromtimestamp(int(time.time())))
    connections.execute("update manager set firstprob=?, lastprob=? where (ip=? and port=?)",(start, finish, ip, port))
    connections.commit()
if  __name__=='__main__':
    while True:
      establish_connection('ourdb.db')
      time.sleep(60)
	  