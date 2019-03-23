import os
from jinja2 import Environment, PackageLoader,FileSystemLoader
from yaml import load,Loader

# Capture our current directory
cwd = os.path.dirname(os.path.abspath(__file__))

def get_certificate(name):
    pem_file = os.path.join(os.pardir,"cfssl/keys/{name}".format(name=name))
    with open(pem_file,'r') as f:
        list_ = f.read().splitlines()
        return "          ".join(
                            [str(x.strip()) + '\n' for x in list_],
                        )

def run_render():
    with open(os.path.join(cwd,'config.yml'),'r') as f: config = load(f, Loader=Loader)    
    j2_env = Environment(loader=FileSystemLoader(os.path.join(cwd,"templates/keys")),trim_blocks=True)
    for hostname in config['etcd'].keys():
        etcd_internal_ip=config['etcd'][hostname]["ip"]
        etcd_endpoints       = 'https://{}:2379'.format(etcd_internal_ip)
        etcd_initial_cluster = '{}=https://{}:2380'.format(hostname, etcd_internal_ip)

        peers = []
        for key in sorted(config['etcd'].keys()):
            if key != hostname:
                ip = config['etcd'][key]['ip']
                peers.append((key, ip))
                etcd_endpoints       = etcd_endpoints       + ',https://{}:2379'.format(ip)
                etcd_initial_cluster = etcd_initial_cluster + ',{}=https://{}:2380'.format(key, ip)        #                        )
            out_file = os.path.join(cwd,"init_coreos_nodes/etcd-{}.yml".format(hostname))
            with open(out_file, 'w') as f:
                f.write(
                    j2_env.get_template("etcd-template.yml").render(
                            hostname=hostname,
                            internal_IP=etcd_internal_ip,
                            peers=peers,
                            initial_cluster=etcd_initial_cluster,
                            etcd_endpoints=etcd_endpoints,
                            ssh_public_key=config['global']["ssh_public_key"],
                            password_hash=config['global']["password_hash"],
                            ca=get_certificate("ca.pem"),
                            etcd_nodes=get_certificate("etcd.pem"),
                            etcd_nodes_key=get_certificate("etcd-key.pem")
                    )
                )
    for hostname in config['api-servers'].keys():
        out_file = os.path.join(cwd,"init_coreos_nodes/kube-{}.yml".format(hostname))
        with open(out_file, 'w') as f:
            f.write(
                j2_env.get_template("kube-apiserver-template.yml").render(
                        hostname=hostname,
                        internal_IP=config['api-servers'][hostname]['ip'],
                        peers=peers,
                        etcd_endpoints=etcd_endpoints,
                        ssh_public_key=config['global']["ssh_public_key"],
                        password_hash=config['global']["password_hash"],
                        # ca
                        ca=get_certificate("ca.pem"),
                        ca_key=get_certificate("ca-key.pem"),
                        # etcd
                        etcd_nodes=get_certificate("etcd.pem"),
                        etcd_nodes_key=get_certificate("etcd-key.pem"),
                        # api
                        apiserver=get_certificate("kubernetes.pem"),
                        apiserver_key=get_certificate("kubernetes-key.pem"),
                        # service account for tls authorization
                        service_account=get_certificate("service-account.pem"),
                        service_account_key=get_certificate("service-account-key.pem"),
                        # kube controller
                        kube_controller_manager=get_certificate("kube-controller-manager.pem"),
                        kube_controller_manager_key=get_certificate("kube-controller-manager-key.pem"),
                )
            )


def main():
    pass
if __name__ == "__main__":
   main()