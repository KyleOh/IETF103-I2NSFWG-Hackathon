#-*- coding: utf-8 -*-

from flask import Flask
from flask import jsonify
from flask_restful import reqparse
from flask_restful import abort
from flask_restful import Api
from flask_restful import Resource

import subprocess
import datetime
import time
import logging
import re
import fileinput
import random


logging.basicConfig(level=logging.DEBUG)
debug_logger = logging.getLogger(__name__)
debug_logger.setLevel(logging.DEBUG)

app = Flask(__name__)
api = Api(app)


# NSF List for Demo
class Vnfs(object):
    def __init__(self, vnf_count, vnf_name, vnf_ip):
        self.vnf_count = vnf_count
        self.vnf_name = vnf_name
        self.vnf_ip = vnf_ip


# Exception
def authenticate_if_not():
    cmd = 'source /opt/stack/devstack/openrc admin admin 1234'
    bash_command(cmd)

# Bash Command Function for using bash shell
def bash_command(cmd):
    subprocess.Popen(['/bin/bash', '-c', cmd])

def get_client_ip(client_name='http_client'):
    debug_logger.info("get_client_ip()")
    cmd = ['openstack', 'server', 'list']
    proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(['grep', client_name], stdin=proc1.stdout, stdout=subprocess.PIPE)
    proc3 = subprocess.Popen(['grep', '-Eo', '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'], stdin=proc2.stdout, stdout=subprocess.PIPE)
    result = proc3.stdout.read()
    # TODO - Hard Coded
    result = '$VAR_A'
    return result

def get_net_src_port_id(client_ip=None):
    if client_ip is None:
        return -1  
    cmd = ['openstack', 'port', 'list']
    proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(['grep', client_ip], stdin=proc1.stdout, stdout=subprocess.PIPE)
    result = proc2.stdout.read().strip().split()[1]
    result = '$VAR_B'
    return result

def replace_default_vars_in_vnffgd(desc_main_var=None,
                                   forwarding_path_name_var='forwarder_name',
                                   desc_for_path_var='desc',
                                   prop_id_var=50,
                                   crit_name_var='vnf_to_vnf',
                                   net_src_port_id_var=None,
                                   dest_port_range_var=None,
                                   ip_proto_var=None,
                                   ip_dest_prefix_var=None,
                                   forwarder_1_var=None,
                                   capa_1_var=None,
                                   forwarder_2_var=None,
                                   capa_2_var=None,
                                   virt_link_1_var=None,
                                   virt_link_2_var=None,
                                   con_point_1_var=None,
                                   con_point_2_var=None,
                                   const_vnfd_1_var=None,
                                   const_vnfd_2_var=None,
                                   icmp_enabled=True,
                                   none_enabled=False):

    if icmp_enabled is True and none_enabled is False:
        file_name = 'tmp_icmp_vnffgd.yaml'
        file_template = '/home/$VAR_C/i2nsf/icmp_vnffgd_template.yaml'
    elif icmp_enabled is True and none_enabled is True:
        file_name = 'tmp_none_icmp_vnffgd.yaml'
        file_template = '/home/$VAR_C/i2nsf/none_icmp_vnffgd_template.yaml'
    elif icmp_enabled is False and none_enabled is True:
        file_name = 'tmp_none_vnffgd.yaml'
        file_template = '/home/$VAR_C/i2nsf/none_vnffgd_template.yaml'
    else:
        file_name = 'tmp_vnffgd.yaml'
        file_template = '/home/$VAR_C/i2nsf/vnffgd_template.yaml'

    with open(file_name, 'w+') as vnffgd_file:
        for line in fileinput.input(files=file_template):
            line = re.sub('DESC_MAIN_VAR', desc_main_var, line.rstrip())
            line = re.sub('FORWARDING_PATH_NAME_VAR', forwarding_path_name_var, line.rstrip())
            line = re.sub('DESC_FOR_PATH_VAR', desc_for_path_var, line.rstrip())
            line = re.sub('PROP_ID_VAR', str(prop_id_var), line.rstrip())
            line = re.sub('CRIT_NAME_VAR', crit_name_var, line.rstrip())
            line = re.sub('NET_SRC_PORT_ID_VAR', net_src_port_id_var, line.rstrip())
            line = re.sub('IP_PROTO_VAR', str(ip_proto_var), line.rstrip())
            line = re.sub('IP_DEST_PREFIX_VAR', ip_dest_prefix_var, line.rstrip())
            line = re.sub('FORWARDER_1_VAR', forwarder_1_var, line.rstrip())
            line = re.sub('CAPA_1_VAR', capa_1_var, line.rstrip())
            line = re.sub('VIRT_LINK_1_VAR', virt_link_1_var, line.rstrip())
            line = re.sub('CON_POINT_1_VAR', con_point_1_var, line.rstrip())
            line = re.sub('CONST_VNFD_1_VAR', const_vnfd_1_var, line.rstrip())
            if icmp_enabled is not True: #When it comes to ICMP, dest_port_range_var is not needed.
                line = re.sub('DEST_PORT_RANGE_VAR', dest_port_range_var, line.rstrip())
            if none_enabled is not True:
                line = re.sub('FORWARDER_2_VAR', forwarder_2_var, line.rstrip())
                line = re.sub('CAPA_2_VAR', capa_2_var, line.rstrip())
                line = re.sub('VIRT_LINK_2_VAR', virt_link_2_var, line.rstrip())
                line = re.sub('CON_POINT_2_VAR', con_point_2_var, line.rstrip())
                line = re.sub('CONST_VNFD_2_VAR', const_vnfd_2_var, line.rstrip())
            vnffgd_file.write(line+'\n')
            print(line)
        return file_name

def create_vnffgd(file_name='tmp_vnffgd.yaml', nsf_id1=None, nsf_id2=None):
    vnffgd_name =  nsf_id1+'-to-'+nsf_id2+'-vnffgd'+str(random.randrange(1,50000))
    debug_logger.info("create_vnffgd() " + vnffgd_name)
    cmd = ['openstack', 'vnf', 'graph', 'descriptor', 'create', '--vnffgd-file', file_name, vnffgd_name]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    time.sleep(2)
    return vnffgd_name

def get_vnf_status(vnf_name=None):
    if vnf_name is None:
        return -1
    debug_logger.info("get_vnf_status() " + vnf_name)
    cmd = ['openstack', 'vnf', 'show', vnf_name, '-f', 'value', '-c', 'status']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    vnf_status = proc.stdout.read()
    vnf_status = vnf_status.rstrip()
    debug_logger.info("VNF STATUS : " + str(vnf_status))
    return str(vnf_status)

def create_vnf_name(nsf_id=None):
    if nsf_id is None:
        return -1
    debug_logger.info("create_vnf_name()")
    vnf_name = 'VNF' + nsf_id + str(random.randrange(1,999999))
    debug_logger.info("create_vnf_name(): " + vnf_name)
    return vnf_name

def create_vnfs(vnfd_name=None, vnf_name=None):
    if vnfd_name is None or vnf_name is None:
        return -1
    debug_logger.info("create_vnfs() " + vnfd_name + ' ' + vnf_name)
    cmd = ['openstack', 'vnf', 'create', '--vnfd-name', vnfd_name, vnf_name]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    # WAIT UNTIL VNF CREATION COMPLETE
    timeout = 120
    vnf_status = get_vnf_status(vnf_name=vnf_name)
    while timeout >= 0 and vnf_status != 'ACTIVE':
        debug_logger.info("WAITING FOR VNF " + vnf_name + " time_left : " + str(timeout))
        vnf_status = get_vnf_status(vnf_name=vnf_name)
        timeout = timeout - 1
        time.sleep(1)
    return vnf_name

def get_vnf_id(vnf_name=None):
    debug_logger.info("get_vnf_id() " + vnf_name)
    cmd = ['openstack', 'vnf', 'list']
    proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(['grep', vnf_name], stdin=proc1.stdout, stdout=subprocess.PIPE)
    result = proc2.stdout.read().strip().split()[1]
    return result

def create_vnffg(vnffgd_name=None, vnfd1_name=None, vnfd2_name=None, vnf1_name=None, vnf2_name=None, vnffg_name=None, icmp_enabled=False, none_enabled=False):
    if vnffgd_name is None:
        return -1
    debug_logger.info("create_vnffg()")
    if none_enabled is True:
        vnf1_id = get_vnf_id(vnf1_name)
        vnf_mapping_info = vnfd1_name + ":" + vnf1_id
    else:
        vnf1_id = get_vnf_id(vnf1_name)
        vnf2_id = get_vnf_id(vnf2_name)
        vnf_mapping_info = vnfd1_name + ":" + vnf1_id + "," + vnfd2_name + ":" + vnf2_id
    
    debug_logger.info("vnf_mapping_info : " + vnf_mapping_info)

    if icmp_enabled is not True:
        cmd = ['openstack', 'vnf', 'graph', 'create', '--vnffgd-name', vnffgd_name, '--vnf-mapping', vnf_mapping_info, '--symmetrical', vnffg_name]
    else:
        cmd = ['openstack', 'vnf', 'graph', 'create', '--vnffgd-name', vnffgd_name, '--vnf-mapping', vnf_mapping_info, vnffg_name]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    result = proc.stdout.read()
    time.sleep(3)
    return result

def get_vnf_ip(vnf_name=None):
    debug_logger.debug("get_vnf_ip()")
    if vnf_name is None:
        return -1
    cmd = ['openstack', 'vnf', 'show', '-f', 'value', '-c', 'mgmt_url', vnf_name]
    proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    proc1.wait()
    vnf_ip_raw_data = proc1.stdout.read()
    # Process ip raw data to real ip
    vnf_ip_raw_data = str(vnf_ip_raw_data).partition(' ')[2] # vnf_ip_data = '"10.0.10.0"}'
    vnf_ip_raw_data = str(vnf_ip_raw_data).replace('"',"") # vnf_ip_data = '10.0.10.0}'
    vnf_ip_raw_data = str(vnf_ip_raw_data).replace("\n","")
    vnf_ip = str(vnf_ip_raw_data).replace('}', "") # vnf_ip = '10.0.10.0'
    return vnf_ip

def get_vnfs_ip(vnf_names_list=None):
    debug_logger.debug("get_vnfs_ip()")
    vnfs_info = []
    if vnf_names_list is None:
        return -1
    for cnt, vnf_name in enumerate(vnf_names_list):
        vnf_ip = get_vnf_ip(vnf_name)
        vnf_info = Vnfs(vnf_count=cnt, vnf_name=vnf_name, vnf_ip=vnf_ip)
        vnfs_info.append(vnf_info)
    return vnfs_info

parser = reqparse.RequestParser()
parser.add_argument('nsf_name', type=str)
parser.add_argument('vnfd_name', type=str)


# Nsf
class Nsf(Resource):
    def get(self, nsf_id1, nsf_id2, ip_proto):
        #abort_if_nsf_doesnt_exist(nsf_id1)
        #authenticate_if_not()

        #0. GET SRC PORT ID INFO and IP DST PREFIX and ICMP_ENABLED
        #   CHECK IF nsf_id2 is "none"
        client_ip = get_client_ip(client_name='client-vm')
        net_src_port_id_var = get_net_src_port_id(client_ip=client_ip)
        #Todo - Hard Coded
        ip_dest_prefix_var='$VAR_D'

        if int(ip_proto) == 1:
            icmp_enabled = True
        else:
            icmp_enabled = False

        if nsf_id2 == "none": #TODO
            none_enabled = True
        else:
            none_enabled = False


        #1. CREATE VNFFGD
        #TODO vnffgd Name setting is needed
        vnffgd_file_name = replace_default_vars_in_vnffgd(desc_main_var=nsf_id1+' to '+nsf_id2,
                                                          forwarding_path_name_var='Forwarding_path_'+nsf_id1+'_to_'+nsf_id2,
                                                          desc_for_path_var='creates path',
                                                          prop_id_var=random.randrange(1,65536),
                                                          crit_name_var='I2NSF'+str(random.randrange(1,65536)),
                                                          net_src_port_id_var=net_src_port_id_var,
                                                          dest_port_range_var='80-1024',
                                                          ip_proto_var=int(ip_proto),
                                                          ip_dest_prefix_var=ip_dest_prefix_var,
                                                          forwarder_1_var='$VAR_E'+nsf_id1[3],
                                                          capa_1_var='CP'+nsf_id1[3]+'2',
                                                          forwarder_2_var='$VAR_E'+nsf_id2[3],
                                                          capa_2_var='CP'+nsf_id2[3]+'2',
                                                          virt_link_1_var='VL'+nsf_id1[3]+'2',
                                                          virt_link_2_var='VL'+nsf_id2[3]+'2',
                                                          con_point_1_var='CP'+nsf_id1[3]+'2',
                                                          con_point_2_var='CP'+nsf_id2[3]+'2',
                                                          const_vnfd_1_var='$VAR_E'+nsf_id1[3],
                                                          const_vnfd_2_var='$VAR_E'+nsf_id2[3],
                                                          icmp_enabled=icmp_enabled,
                                                          none_enabled=none_enabled
                                                         )

        vnffgd_name = create_vnffgd(file_name=vnffgd_file_name, nsf_id1=nsf_id1, nsf_id2=nsf_id2)

        #2. CREATE VNFs with VNFDs
        vnf_name = create_vnf_name(nsf_id=nsf_id1[3])
        vnf1_name = create_vnfs(vnfd_name='$VAR_E'+nsf_id1[3], vnf_name=vnf_name)
        # TODO : if nsf_id2 is not None:
        if none_enabled is not True:
            vnf_name = create_vnf_name(nsf_id=nsf_id1[3])
            vnf2_name = create_vnfs(vnfd_name='$VAR_E'+nsf_id2[3], vnf_name=vnf_name)

        #3. CREATE VNFFG with VNFFGD and VNFs
        if none_enabled is not True:
            vnffg_name = 'vnffg_' + nsf_id1 + '_' + nsf_id2 + str(random.randrange(1,99999))
            vnffg_result = create_vnffg(vnffgd_name=vnffgd_name, vnfd1_name='$VAR_E'+nsf_id1[3], vnfd2_name='$VAR_E'+nsf_id2[3],
                                        vnf1_name=vnf1_name, vnf2_name=vnf2_name, vnffg_name=vnffg_name, icmp_enabled=icmp_enabled, none_enabled=none_enabled)
            debug_logger.info("vnffg_result[1] : " + vnffg_result)
        else:
            vnffg_name = 'vnffg_' + nsf_id1 + str(random.randrange(1,99999))
            vnffg_result = create_vnffg(vnffgd_name=vnffgd_name, vnfd1_name='$VAR_E'+nsf_id1[3], vnf1_name=vnf1_name,
                                        vnffg_name=vnffg_name, icmp_enabled=icmp_enabled, none_enabled=none_enabled)
            debug_logger.info("vnffg_result[2] : " + vnffg_result)

        #4. GET VNF IPs
        if none_enabled is not True:
            vnfs_name_list = [vnf1_name, vnf2_name]
            vnfs_info = get_vnfs_ip(vnfs_name_list)
            final_result = jsonify(vnf1_name=vnfs_info[0].vnf_name,
                                   vnf1_ip=vnfs_info[0].vnf_ip,
                                   vnf2_name=vnfs_info[1].vnf_name,
                                   vnf2_ip=vnfs_info[1].vnf_ip
                                   )
        else:
            vnfs_name_list = [vnf1_name]
            vnfs_info = get_vnfs_ip(vnfs_name_list)
            final_result = jsonify(vnf1_name=vnfs_info[0].vnf_name,
                                   vnf1_ip=vnfs_info[0].vnf_ip
                                   )
        return final_result

    def delete(self, nsf_id1):
        return '', 204

    def put(self, nsf_id1):
        return '', 201


# URL Router Mapping
api.add_resource(Nsf, '/nsfs/<string:nsf_id1>/<string:nsf_id2>/<string:ip_proto>')

@app.route("/")
def middleman():
    return "I2NSF middleman between SC and DMS"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=$VAR_F)
