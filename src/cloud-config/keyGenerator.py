from shutil import move,rmtree
from urllib import urlretrieve
from subprocess import Popen
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
        print('ete ka chi mtnum')
        cfssl_url = 'https://pkg.cfssl.org/R1.2/cfssl_linux-amd64'
        cfssl_json_url = 'https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64'
        urlretrieve(cfssl_url,'cfssl')
        urlretrieve(cfssl_json_url,'cfssljson')

        os.chmod('cfssl', 755)
        os.chmod('cfssljson', 755)
        move('cfssljson',bin_dir)
        move('cfssl',bin_dir)

def genTLS(crt_name,cwd,config,j2Env):

    keys_dir = os.path.join(cwd,'keys')
    bin_cfssl = os.path.join(cwd,'bin/') + 'cfssl'
    bin_cfssl_json = os.path.join(cwd,'bin/') + 'cfssljson'
    # csr_file = os.path.join(cwd,'templates/keys/{crt_name}-csr.json'.format(crt_name=crt_name))
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
        for worker in config['certificates']['worker']['name']:
            with open(os.path.join(cwd,'templates/keys/{}-csr.json'.format(worker)), 'w') as f:
                f.write(j2Env.get_template("worker-csr.json.j2").render(name=worker))

            csr_file = os.path.join(cwd, 'templates/keys/{}-csr.json'.format(worker))
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
                worker=worker,
                ip=config['worker'][worker]['ip']
            )
    # elif crt_name in config['certificates']['kube-controller-manager']['name']:
    #     for controler in config['certificates']['kube-controller-manager']['name']:
    #         with open(os.path.join(cwd,'templates/keys/{}-csr.json'.format(controler)), 'w') as f:
    #             f.write(j2Env.get_template("kube-controller-manager-csr.json.j2").render(name=controler))
    #
    #         csr_file = os.path.join(cwd, 'templates/keys/{}-csr.json'.format(controler))
    #         gen_bash_cmd = '{bin_cfssl} gencert -ca={ca_crt_file} -ca-key={ca_key_file} ' \
    #                        ' -profile=kubernetes {csr_file} ' \
    #                        '-hostname={worker},{worker}.mkoyan.local,{ip} ' \
    #                        '-config={ca_config} | {bin_cfssl_json} ' \
    #                        '-bare {keys_dir}/{crt_name}'.format(
    #             bin_cfssl=bin_cfssl,
    #             bin_cfssl_json=bin_cfssl_json,
    #             csr_file=csr_file,
    #             keys_dir=keys_dir,
    #             ca_crt_file=ca_crt_file,
    #             ca_key_file=ca_key_file,
    #             crt_name=crt_name,
    #             ca_config=ca_config,
    #             worker=worker,
    #             ip=config['worker'][worker]['ip']
    #         )




    process = Popen(gen_bash_cmd, shell=True, stdout=DEVNULL,stdin=DEVNULL,stderr=DEVNULL)
    process.communicate()


    # csr = os.path.join(cwd,'templates/keys/ca-csr.json')
    # gen_bash_ca = '{bin_cfssl} gencert -initca {csr} | {bin_cfssl_json} -bare {keys_dir}/ca'.format(bin_cfssl=bin_cfssl,bin_cfssl_json=bin_cfssl_json,csr=csr,keys_dir=keys_dir)
    # process = Popen(gen_bash_ca, shell=True, stdout=DEVNULL,stdin=DEVNULL,stderr=DEVNULL)
    # process.communicate()

def genKeys(cwd,config,j2Env):
    keys_dir = os.path.join(cwd,'keys')
    if not os.path.exists(keys_dir):
        os.mkdir(keys_dir)
        
    leaves = []
    for key in config['certificates']:
        for name in config['certificates'][key].values():
            for item in name:
                leaves.append(item)
    # run bash for each crt
    for leaf in leaves:
        genTLS(crt_name=leaf,cwd=cwd,config=config,j2Env=j2Env)
def main():
    pass
if __name__ == "__main__":
   main()