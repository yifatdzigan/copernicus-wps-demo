import os
import glob
import sys
import zipfile

from jinja2 import Environment, PackageLoader, select_autoescape

from pywps import configuration

import logging
LOGGER = logging.getLogger("PYWPS")

template_env = Environment(
    loader=PackageLoader('copernicus', '/templates/esmvaltool'),
    autoescape=select_autoescape(['yml', ])
)

VERSION = "2.0.0"


def run(recipe_file, config_file):
    """Run esmvaltool"""
    from esmvaltool._main import configure_logging, read_config_user_file, process_recipe
    recipe_name = os.path.splitext(os.path.basename(recipe_file))[0]
    cfg = read_config_user_file(config_file, recipe_name)

    # Create run dir
    if os.path.exists(cfg['run_dir']):
        print("ERROR: run_dir {} already exists, aborting to "
              "prevent data loss".format(cfg['run_dir']))
    os.makedirs(cfg['run_dir'])

    # configure logging
    configure_logging(
        output=cfg['run_dir'], console_log_level=cfg['log_level'])

    # log header
    # LOGGER.info(__doc__)
    LOGGER.debug("Using config file %s", config_file)

    # check NCL version
    # ncl_version_check()

    cfg['synda_download'] = False

    try:
        LOGGER.info("run esmvaltool ...")
        process_recipe(recipe_file=recipe_file, config_user=cfg)
        LOGGER.info("esmvaltool ... done.")
    except Exception as err:
        LOGGER.exception('esmvaltool failed!')
        #For debugging purposes, exit here to keep the temp folder
        #Should ideally be an option in PyWPS
        #sys.exit(1)
        raise Exception('esmvaltool failed: {0}'.format(err))
    # find the log
    logfile = os.path.join(cfg['run_dir'], 'main_log.txt')
    return logfile, cfg['plot_dir'], cfg['work_dir'], cfg['run_dir']


def generate_recipe(diag, constraints=None, options=None, start_year=2000, end_year=2005, output_format='pdf', workdir=None):
    constraints = constraints or {}
    workdir = workdir or os.curdir
    workdir = os.path.abspath(workdir)
    output_dir = os.path.join(workdir, 'output')
    # write config.yml
    config_templ = template_env.get_template('config.yml')
    rendered_config = config_templ.render(
        archive_root=configuration.get_config_value("data", "archive_root"),
        obs_root=configuration.get_config_value("data", "obs_root"),
        output_dir=output_dir,
        output_format=output_format,
    )
    config_file = os.path.abspath(os.path.join(workdir, "config.yml"))
    with open(config_file, 'w') as fp:
        fp.write(rendered_config)

    # write recipe.xml
    recipe = 'recipe_{0}.yml'.format(diag)
    recipe_templ = template_env.get_template(recipe)
    rendered_recipe = recipe_templ.render(
        diag=diag,
        workdir=workdir,
        constraints=constraints,
        start_year=start_year,
        end_year=end_year,
	options=options,
    )
    recipe_file = os.path.abspath(os.path.join(workdir, "recipe.yml"))
    with open(recipe_file, 'w') as fp:
        fp.write(rendered_recipe)
    return recipe_file, config_file


def get_output(output_dir, path_filter, name_filter=None, output_format='pdf'):
    name_filter = name_filter or '*'
    # output/recipe_20180130_111116/plots/diagnostic1/script1/MultiModelMean_T3M_ta_2001-2002_mean.pdf
    output_filter = os.path.join(
        output_dir, path_filter, '{0}.{1}'.format(name_filter, output_format))
    LOGGER.debug("output_fitler %s", output_filter)
    matches = glob.glob(output_filter)
    if len(matches) == 0:
        LOGGER.info("output_dir=%s", output_dir)
        raise Exception("no output found in output dir.")
    elif len(matches) > 1:
        LOGGER.warn("more then one output found %s", matches)
    LOGGER.debug("output found=%s", matches[0])
    return matches[0]

def compress_output(output_dir, archive_file):
    with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as ziph:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                path = os.path.join(root, file)
                arcname = os.path.relpath(path, output_dir)
                ziph.write(path, arcname)

    return archive_file

