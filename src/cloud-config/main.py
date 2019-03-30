from configGenerator import *
from optparse import OptionParser
from keyGenerator import *
from yaml import load
import yamlordereddictloader
from jinja2 import Environment,FileSystemLoader


def string2Bool(_string):
    if _string == 'True':
        return True
    return False


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cwd, 'config.yml'), 'r') as f: config = load(f, Loader=yamlordereddictloader.Loader)
    j2_env = Environment(loader=FileSystemLoader(os.path.join(cwd)), trim_blocks=True)

    parser = OptionParser()
    parser.add_option("-b","--updateBin",
                      dest='updateBin',
                      help="Update Bins",
                      default=False)
    parser.add_option("-c","--updateCrts",
                      dest='updateCrts',
                      help="Update Certificates",
                      default=False)

    (options, args) = parser.parse_args()
    updateBin = string2Bool(options.updateBin)
    updateCrts = string2Bool(options.updateCrts)


    getBinaries(cwd,updateBin)
    genKeys(cwd, config, j2_env,updateCrts)

    # render cloud-configs
    run_render(config,j2_env)

# bash
# for instance in etcd-1 etcd-2 etcd-3 kube-apiservers-1; do ./esxi-vm-create -H 10.100.100.168 -U root -P Class@123456 -n $instance -N inet_300 --summary --iso coreos_production_iso_image.iso;done

if __name__ == "__main__":
    main()