#!/usr/bin/env python
# File created on 27 Oct 2009.
from __future__ import division

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2011, The QIIME Project"
__credits__ = ["Greg Caporaso"]
__license__ = "GPL"
__version__ = "1.6.0-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Development"

from qiime.util import make_option
from os import makedirs
from qiime.util import (load_qiime_config, 
                        parse_command_line_parameters, 
                        get_options_lookup)
from qiime.parse import parse_qiime_parameters
from qiime.workflow import (print_commands,
                            call_commands_serially, 
                            print_to_stdout, 
                            no_status_updates,
                            validate_and_set_jobs_to_start)
from qiime.core_diversity_analyses import run_core_diversity_analyses

qiime_config = load_qiime_config()
options_lookup = get_options_lookup()

script_info={}
script_info['brief_description'] = """A workflow for running a core set of QIIME diversity analyses."""
script_info['script_description'] = """This script plugs several QIIME diversity analyses together to form a basic workflow beginning with a BIOM table, mapping file, and optional phylogenetic tree."""

script_info['script_usage'] = []

script_info['script_usage'].append(("","Run diversity analyses at 20 sequences/sample, with categorical analyses focusing on the SampleType and day categories. ALWAYS SPECIFY ABSOLUTE FILE PATHS (absolute path represented here as $PWD, but will generally look something like /home/ubuntu/my_analysis/).","%prog -i $PWD/otu_table.biom -o $PWD/core_output -m $PWD/map.txt -c SampleType,day -t $PWD/rep_set.tre -e 20"))

script_info['script_usage_output_to_remove'] = ['$PWD/core_output']

script_info['output_description'] =""""""

script_info['required_options'] = [
 make_option('-i','--input_biom_fp',type='existing_filepath',
    help='the input biom file [REQUIRED]'),
 make_option('-o','--output_dir',type='new_dirpath',
    help='the output directory [REQUIRED]'),
 make_option('-m','--mapping_fp',type='existing_filepath',
    help='the mapping filepath [REQUIRED]'),
 make_option('-e','--sampling_depth',type='int',default=None,
    help=('Sequencing depth to use for even sub-sampling and maximum'
          ' rarefaction depth. You should review the output of'
          ' print_biom_table_summary.py to decide on this value.')),
    ]

script_info['optional_options'] = [\
 make_option('-p','--parameter_fp',type='existing_filepath',
    help=('path to the parameter file, which specifies changes'
          ' to the default behavior. For more information, see'        
          ' www.qiime.org/documentation/qiime_parameters_files.html'
          ' [if omitted, default values will be used]')),
 make_option('-a','--parallel',action='store_true',default=False,
    help=('Run in parallel where available. Specify number of'
          ' jobs to start with -O or in the parameters file.'
          ' [default: %default]')),
 make_option('--nonphylogenetic_diversity',action='store_true',default=False,
    help=('Apply non-phylogenetic alpha and beta diversity calculations. This'
          ' is useful if, for example, you are working with non-amplicon BIOM'
          ' tables, or if a reliable tree is not available (e.g., if you\'re '
          ' working with ITS amplicons) [default: %default]')),
 make_option('-t','--tree_fp',type='existing_filepath',
    help=('Path to the tree file if one should be used.'
          ' [default: no tree will be used]')),
 make_option('-c','--categories', type='string',
    help=('The metadata category or categories to compare'
          ' (i.e., column headers in the mapping file)'
          ' for the otu_category_significance,'
          ' supervised_learning.py, and cluster_quality.py steps.'
          ' Pass a comma-separated list if more than one category'
          ' [default: %default; skip these steps]')),
 options_lookup['jobs_to_start_workflow']
]
script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)

    verbose = opts.verbose
    
    input_biom_fp = opts.input_biom_fp
    output_dir = opts.output_dir
    categories = opts.categories
    if categories != None:
        categories = categories.split(',')
    tree_fp = opts.tree_fp
    mapping_fp = opts.mapping_fp
    verbose = opts.verbose
    parallel = opts.parallel
    sampling_depth = opts.sampling_depth
    nonphylogenetic_diversity = opts.nonphylogenetic_diversity
    
    if opts.parameter_fp != None:
        try:
            parameter_f = open(opts.parameter_fp)
        except IOError:
            raise IOError,\
             "Can't open parameters file (%s). Does it exist? Do you have read access?"\
             % opts.parameter_fp
        params = parse_qiime_parameters(parameter_f)
    else:
        params = parse_qiime_parameters([])
    
    if nonphylogenetic_diversity:
        params['beta_diversity']['metrics'] = 'bray_curtis'
        params['alpha_diversity']['metrics'] = 'observed_species,chao1'
    
    jobs_to_start = opts.jobs_to_start
    default_jobs_to_start = qiime_config['jobs_to_start']
    validate_and_set_jobs_to_start(params,
                                   jobs_to_start,
                                   default_jobs_to_start,
                                   parallel,
                                   option_parser)
    
    try:
        makedirs(output_dir)
    except OSError:
        option_parser.error("Output directory already exists. Please choose"
            " a different directory, or force overwrite with -f.")
        
    command_handler = call_commands_serially
    
    if verbose:
        status_update_callback = print_to_stdout
    else:
        status_update_callback = no_status_updates
    
    run_core_diversity_analyses(
        biom_fp=input_biom_fp,
        mapping_fp=mapping_fp,
        sampling_depth=sampling_depth,
        output_dir=output_dir,
        qiime_config=load_qiime_config(),
        command_handler=command_handler,
        tree_fp=tree_fp,
        params=params,
        categories=categories,
        arare_min_rare_depth=10,
        arare_num_steps=10,
        parallel=parallel,
        status_update_callback=status_update_callback)

if __name__ == "__main__":
    main()    
