from configGenerator import *
from optparse import OptionParser
from keyGenerator import *
from yaml import load
import yamlordereddictloader
from jinja2 import Environment,FileSystemLoader


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cwd, 'config.yml'), 'r') as f: config = load(f, Loader=yamlordereddictloader.Loader)
    j2_env = Environment(loader=FileSystemLoader(os.path.join(cwd, "templates/keys")), trim_blocks=True)

    parser = OptionParser()
    parser.add_option("-u", "--updateBin",
                      dest='updateBin',
                      help="Update Bins",
                      default=False)


    (options, args) = parser.parse_args()
    getBinaries(cwd, updateBin=options.updateBin)
    genKeys(cwd, config, j2_env)

if __name__ == "__main__":
    main()