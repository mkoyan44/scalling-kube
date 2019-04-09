from shutil import rmtree
from subprocess import Popen
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

cwd = os.path.dirname(os.path.abspath(__file__))

def get_certificate(name):
    pem_file = os.path.join(cwd,'keys/', name)
    with open(pem_file,'r') as f:
        list_ = f.read().splitlines()
        return "         ".join(
                            [str(x.rstrip()) + '\n' for x in list_],
                        )

def run_render(config,j2_env):
    # global vars
    _hosts_list = []

    # leaves = []
    # for key in config['certificates']:
    #     for name in config['certificates'][key].values():
    #         for item in name:
    #             leaves.append(item)

    render_dir  = os.path.join(cwd,'init_coreos_nodes/')
    if not os.path.exists(render_dir):
        rmtree(render_dir,ignore_errors=True)
        os.mkdir(render_dir)

    computers = {}
    computers.update(config['etcd'])
    computers.update(config['kube-apiservers'])
    computers.update(config['kube-workers'])
    for computer in computers.keys():
        _hosts_list.append((computers[computer]['hostname'], computers[computer]['ip']))


    etcd_hosts_list = []
    etcd_initial_cluster = []
    etcd_endpoints = []
    for hostname in config['etcd'].keys():
        ip=config['etcd'][hostname]["ip"]
        etcd_hosts_list.append((hostname, ip))
        etcd_initial_cluster.append('{}=https://{}:2380'.format(hostname, ip))
        etcd_endpoints.append('https://{}:2379'.format(ip))

    for hostname in config['etcd'].keys():
        out_file = os.path.join(render_dir,"{}.yml".format(hostname))
        with open(out_file, 'w') as f:
            f.write(
                j2_env.get_template("templates/kube/etcd-template.yml").render(
                    hostname=hostname,
                    internal_IP=config['etcd'][hostname]['ip'],
                    _hosts_list=_hosts_list,
                    initial_cluster=','.join(etcd_initial_cluster),
                    etcd_endpoints=','.join(etcd_endpoints),
                    ssh_public_key=config['global']["ssh_public_key"],
                    password_hash=config['global']["password_hash"],
                    ca=get_certificate("ca.pem"),
                    etcd_nodes=get_certificate("etcd.pem"),
                    etcd_nodes_key=get_certificate("etcd-key.pem"),
                )
            )
        translateToIgnition(hostname)

    for hostname in config['kube-apiservers'].keys():
        out_file = os.path.join(render_dir, "{}.yml".format(hostname))
        with open(out_file, 'w') as f:
            f.write(
                j2_env.get_template("templates/kube/kube-apiserver-template.yml").render(
                    hostname=hostname,
                    internal_IP=config['kube-apiservers'][hostname]['ip'],
                    _hosts_list=_hosts_list,
                    etcd_endpoints=','.join(etcd_endpoints),
                    ssh_public_key=config['global']["ssh_public_key"],
                    password_hash=config['global']["password_hash"],
                    # ca
                    ca=get_certificate("ca.pem"),
                    ca_key=get_certificate("ca-key.pem"),
                    # etcd
                    etcd_nodes=get_certificate('etcd.pem'),
                    etcd_nodes_key=get_certificate('etcd-key.pem'),

                    # api
                    apiserver=get_certificate('kube-apiservers.pem'),
                    apiserver_key=get_certificate('kube-apiservers-key.pem'),

                    # service account for tls authorization
                    service_account=get_certificate("service-account.pem"),
                    service_account_key=get_certificate("service-account-key.pem"),
                    # kube controller
                    kube_controller_manager=get_certificate("kube-controller-manager.pem"),
                    kube_controller_manager_key=get_certificate("kube-controller-manager-key.pem"),
                )
            )
        translateToIgnition(hostname)


    for hostname in config['kube-workers'].keys():
        out_file = os.path.join(render_dir, "{}.yml".format(hostname))
        with open(out_file, 'w') as f:
            f.write(
                j2_env.get_template("templates/kube/kube-worker-template.yml").render(
                    hostname=hostname,
                    internal_IP=config['kube-workers'][hostname]['ip'],
                    _hosts_list=_hosts_list,
                    etcd_endpoints=','.join(etcd_endpoints),
                    ssh_public_key=config['global']["ssh_public_key"],
                    password_hash=config['global']["password_hash"],
                    # ca
                    ca=get_certificate("ca.pem"),
                    ca_key=get_certificate("ca-key.pem"),
                    # etcd
                    etcd_nodes=get_certificate('etcd.pem'),
                    etcd_nodes_key=get_certificate('etcd-key.pem'),

                    # workers
                    worker_cert = get_certificate('worker.pem'),
                    worker_key = get_certificate('worker-key.pem'),

                )
            )
        translateToIgnition(hostname)

def translateToIgnition(hostname):
    render_dir = os.path.join(cwd,'init_coreos_nodes/')
    ct = os.path.join(cwd,'bin/ct')
    ct_bash_cmd = "{ct} -in-file {hostname}.yml  -out-file {hostname}.json -pretty".format(ct=ct,hostname=os.path.join(render_dir,hostname))
    process = Popen(ct_bash_cmd, shell=True, stdout=DEVNULL,stdin=DEVNULL,stderr=DEVNULL)
    process.communicate()

def main():
    pass
if __name__ == "__main__":
   main()