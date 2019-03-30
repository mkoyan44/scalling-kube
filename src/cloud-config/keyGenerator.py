from shutil import move,rmtree
from urllib import urlretrieve
from subprocess import Popen,STDOUT
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')


def getBinaries(cwd,updateBin=False):
    bin_dir = os.path.join(cwd,'bin/')
    if not os.path.exists(bin_dir) or updateBin is True:
        rmtree(bin_dir,ignore_errors=True)
        os.mkdir(bin_dir)
        cfssl_url = 'https://pkg.cfssl.org/R1.2/cfssl_linux-amd64'
        cfssl_json_url = 'https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64'
        ct_url = 'https://github.com/coreos/container-linux-config-transpiler/releases/download/v0.9.0/ct-v0.9.0-x86_64-unknown-linux-gnu'

        urlretrieve(cfssl_url,'cfssl')
        urlretrieve(cfssl_json_url,'cfssljson')
        urlretrieve(ct_url,'ct')

        os.chmod('cfssl', 755)
        os.chmod('cfssljson', 755)
        os.chmod('ct', 755)
        move('cfssljson',bin_dir)
        move('cfssl',bin_dir)
        move('ct', bin_dir)

def genTLS(crt_name,cwd,config,j2Env):
    keys_dir = os.path.join(cwd,'keys')
    bin_cfssl = os.path.join(cwd,'bin/') + 'cfssl'
    bin_cfssl_json = os.path.join(cwd,'bin/') + 'cfssljson'
    ca_config = os.path.join(cwd,'templates/keys/ca-config.json')
    ca_crt_file = os.path.join(cwd,'keys/ca.pem')
    ca_key_file = os.path.join(cwd,'keys/ca-key.pem')

    gen_bash_cmd = ''
    if crt_name in config['certificates']['ca']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/ca-csr.json')
        gen_bash_cmd = '{bin_cfssl} gencert -initca {csr_file} | {bin_cfssl_json} -bare {keys_dir}/{crt_name}'.format(
                                    bin_cfssl=bin_cfssl,
                                    bin_cfssl_json=bin_cfssl_json,
                                    csr_file=csr_file,
                                    keys_dir=keys_dir,
                                    crt_name=crt_name
                                )
    elif crt_name in config['certificates']['admin']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/admin-csr.json')
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes {csr_file} -config={ca_config} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                crt_name=crt_name,
                                                                ca_config=ca_config
                                                            )
    elif crt_name in config['certificates']['worker']['name']:
        with open(os.path.join(cwd,'templates/keys/{}-csr.json'.format(crt_name)), 'w') as f:
            f.write(j2Env.get_template("templates/keys/worker-csr.json.j2").render(name=crt_name))

        csr_file = os.path.join(cwd, 'templates/keys/{}-csr.json'.format(crt_name))
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes {csr_file} ' \
                       '-hostname={worker},{worker}.mkoyan.local,{ip} ' \
                       '-config={ca_config} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
            bin_cfssl=bin_cfssl,
            bin_cfssl_json=bin_cfssl_json,
            csr_file=csr_file,
            keys_dir=keys_dir,
            ca_crt_file=ca_crt_file,
            ca_key_file=ca_key_file,
            crt_name=crt_name,
            ca_config=ca_config,
            worker=crt_name,
            ip=config['worker'][crt_name]['ip']
        )

    elif crt_name in config['certificates']['kube-controller-manager']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/kube-controller-manager-csr.json')
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes -config={ca_config} {csr_file} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                crt_name=crt_name,
                                                                ca_config=ca_config
                                                            )

    elif crt_name in config['certificates']['kube-proxy']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/kube-proxy-csr.json')
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes -config={ca_config} {csr_file} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                crt_name=crt_name,
                                                                ca_config=ca_config
                                                            )

    elif crt_name in config['certificates']['kube-scheduler']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/kube-scheduler-csr.json')
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes -config={ca_config} {csr_file} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                crt_name=crt_name,
                                                                ca_config=ca_config
                                                            )


    elif crt_name in config['certificates']['kube-apiservers']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/kube-apiservers-csr.json')
        apiIps = []
        for apiServer in config['kube-apiservers'].keys():
            apiIps.append(config['kube-apiservers'][apiServer]['ip'])
        apiIps_list = ",".join(apiIps)

        hostnames= "10.3.0.1," \
                   "{hostnames}," \
                   "127.0.0.1," \
                   "{lb}," \
                   "kubernetes,kubernetes.default," \
                   "kubernetes.default.svc," \
                   "kubernetes.default.svc.mkoyan," \
                   "kubernetes.default.svc.mkoyan.local ".format(hostnames=apiIps_list,lb=config['lb']['ip'])
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes -config={ca_config} ' \
                       '-hostname={hostnames}' \
                       '{csr_file} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                crt_name=crt_name,
                                                                ca_config=ca_config,
                                                                hostnames=hostnames
                                                            )

    elif crt_name in config['certificates']['service-account']['name']:
        csr_file = os.path.join(cwd, 'templates/keys/service-account-csr.json')
        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes -config={ca_config} {csr_file} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/{crt_name}'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                crt_name=crt_name,
                                                                ca_config=ca_config
                                                            )

    elif crt_name.startswith('etcd'):
        csr_file = os.path.join(cwd, 'templates/keys/etcd-csr.json')
        etcdIps = []
        for etcdServer in config['etcd']:
            etcdIps.append(config['etcd'][etcdServer]['ip'])
        etcdIpsList = ",".join(etcdIps)

        hostnames= "{hostnames},127.0.0.1 ".format(hostnames=etcdIpsList)

        gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
                       ' -profile=kubernetes -config={ca_config} ' \
                       '-hostname={hostnames}' \
                       '{csr_file} | {bin_cfssl_json} ' \
                       '-bare {keys_dir}/etcd'.format(
                                                                bin_cfssl=bin_cfssl,
                                                                bin_cfssl_json=bin_cfssl_json,
                                                                csr_file=csr_file,
                                                                keys_dir=keys_dir,
                                                                ca_crt_file=ca_crt_file,
                                                                ca_key_file=ca_key_file,
                                                                ca_config=ca_config,
                                                                hostnames=hostnames
                                                            )
    process = Popen(gen_bash_cmd, shell=True,stdout=DEVNULL,stdin=DEVNULL,stderr=DEVNULL)
    process.communicate()

def genKeys(cwd,config,j2Env,updateCrts):
    keys_dir = os.path.join(cwd,'keys')
    if not os.path.exists(keys_dir):
        os.mkdir(keys_dir)

    leaves = []
    for key in config['certificates']:
        for name in config['certificates'][key].values():
            for item in name:
                if item.startswith('ca'):
                    leaves.insert(0, item)
                elif item.startswith('etcd'):
                    leaves.append('etcd')
                else:
                    leaves.append(item)


    # remove duplicates
    def unique(sequence):
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]
    leaves = unique(leaves)

    # run bash for each crt
    for leaf in leaves:
        full_name = os.path.join(keys_dir, '{}.pem'.format(leaf))
        if not os.path.isfile(full_name) or updateCrts is True:
            genTLS(crt_name=leaf,cwd=cwd,config=config,j2Env=j2Env)


def main():
    pass
if __name__ == "__main__":
   main()