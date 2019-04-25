# -*- coding: utf-8 -*-
import json
import requests
import datetime
import subprocess
import xml.etree.ElementTree as ET

from keystoneauth1.identity import v3
from keystoneauth1 import session as keystone_session

from xlwt import Workbook
from keystoneclient import client as keystone_client
from cinderclient import client as cinder_client
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

CLOUDS = {"uos": {"os_auth_url": "http://localhost:35357/v3",
                  "regions": ["regionOne"],
                  "admin_user": "admin",
                  "admin_password": "password",
                  "admin_tenant_name": "admin"},
}


def wrap_exception(default_return_value=[]):
    def wrapper(f):
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                return default_return_value
        return inner
    return wrapper


def get_session(cloud):
    auth = v3.Password(auth_url=cloud['os_auth_url'],
                       username=cloud['admin_user'],
                       password=cloud['admin_password'],
                       project_name=cloud['admin_tenant_name'],
                       project_domain_name="Default",
                       user_domain_name="Default")
    return keystone_session.Session(auth=auth)


def get_keystoneclient(session):
    return keystone_client.Client("3.1",
                                  session=session)

@wrap_exception()
def get_user_list(client):
    return client.users.list()


@wrap_exception()
def get_role_assignment_list(client, user=None, project=None):
    return client.role_assignments.list(user=user,
                                        project=project,
                                        include_names=True)

@wrap_exception()
def get_user_from_kunkka(user_id):
    CMD = ['ssh', 'heat-admin@overcloud-controller-0', 'sudo', 'mysql', 'kunkka', '-e', '\'select * from users where id="%s"\'' % user_id, '--xml']
    o = subprocess.check_output(CMD)
    root = ET.fromstring(o)
    if len(root) > 0:
        phone = root[0][1].text or ""
        email = root[0][2].text or ""
        name = root[0][4].text or ""
        full_name = root[0][10].text or ""
        company = root[0][11].text or ""
    else:
        return

    return dict(id=user_id, phone=phone,
                email=email, name=name,
                full_name=full_name,
                company=company)


@wrap_exception()
def get_user(client, user_id):
    return client.users.get(user_id)


@wrap_exception()
def get_project_list(client):
    return client.projects.list()


@wrap_exception()
def get_project(client, project_id):
    return client.projects.get(project_id)


def get_novaclient(session, region_name=None):
    return nova_client.Client("2.1",
                              session=session,
                              region_name=region_name)

@wrap_exception()
def server_list(client, project_id=None, region_name=None):
    search_opts = {'all_tenants': 1}

    if project_id:
        search_opts.update(project_id=project_id)

    return client.servers.list(detailed=True,
                               search_opts=search_opts)

@wrap_exception()
def server_get(client, instance_id):
    return client.servers.get(instance_id)


@wrap_exception()
def flavor_get(client, flavor):
    return client.flavors.get(flavor)


def get_cinderclient(session, region_name=None):
    return cinder_client.Client("2",
                                session=session,
                                region_name=region_name)

@wrap_exception()
def volume_get(client, volume_id):
    """To see all volumes in the cloud as admin.
    """
    return client.volumes.get(volume_id)


@wrap_exception()
def volume_list(client, project_id=None):
    """To see all volumes in the cloud as admin.
    """
    search_opts = {'all_tenants': 1}
    if project_id:
       search_opts.update(project_id=project_id)
    return client.volumes.list(detailed=True, search_opts=search_opts)


def get_neutronclient(session, region_name=None):
    return neutron_client.Client(session=session,
                                 region_name=region_name)


@wrap_exception()
def floatingip_list(client, project_id=None):
    if project_id:
        fips = client.list_floatingips(tenant_id=project_id).get('floatingips')
    else:
        fips = client.list_floatingips().get('floatingips')

    return fips

def write_row_to_sheet(j, sheet, item):
    c = 0
    for k in item:
       sheet.write(j, c, k)
       c += 1

book = Workbook(encoding='utf-8')
sheet1 = book.add_sheet('Sheet1')

COLUMNS = [u"资源名称", u"资源ID", u"资源类型", u"资源信息", u"用户ID", u"用户名", u"姓名", u"用户邮箱", u"电话", u"公司", u"项目ID"]

for i in range(len(COLUMNS)):
    sheet1.write(0, i, COLUMNS[i])

j = 1


for cloud_name, cloud in CLOUDS.items():
    session = get_session(cloud)
    for region in cloud['regions']:
        ks_client = get_keystoneclient(session)
        no_client = get_novaclient(session, region_name=region)
        ci_client = get_cinderclient(session, region_name=region)
        ne_client = get_neutronclient(session, region_name=region)

        projects = get_project_list(ks_client)
        for project in projects:
            rs = get_role_assignment_list(ks_client, project=project.id)
            user_id = user = None
            for r in rs:
                if r.role['name'] == 'Member' or r.role['name'] == '_member_':
                    user_id = r.user['id']
                    user = get_user_from_kunkka(user_id)
                    break

            user_id = user_id if user_id else ""
            phone = user['phone'] if user else ""
            email = user['email'] if user else ""
            name = user['name'] if user else ""
            full_name = user['full_name'] if user else ""
            company = user['company'] if user else ""

            item_a = [user_id, name, full_name, email, phone, company, project.id]

            servers = server_list(no_client, project_id=project.id)
            for server in servers:
                flavor = flavor_get(no_client, server.flavor['id'])
                if flavor:
                   vcpus = flavor.vcpus
                   ram = flavor.ram / 1024
                else:
                   vcpus = ""
                   ram = ""
                item_b = [server.name, server.id, u"虚拟机", "%sCPU/%sGB" % (vcpus, ram)]
                item = item_b + item_a
                write_row_to_sheet(j, sheet1, item)
                j += 1

            volumes = volume_list(ci_client, project_id=project.id)
            for volume in volumes:
                item_b = [volume.name, volume.id, u"云硬盘", volume.size]
                item = item_b + item_a
                write_row_to_sheet(j, sheet1, item)
                j += 1

            fips = floatingip_list(ne_client, project_id=project.id)
            for fip in fips:
                item_b = ["", fip['id'], u"公网IP", fip['floating_ip_address']]
                item = item_b + item_a
                write_row_to_sheet(j, sheet1, item)
                j += 1

book.save('report.xls')

