import logging
import os

from pywps import FORMATS, ComplexInput, ComplexOutput, Format, LiteralInput, LiteralOutput, Process
from pywps.app.Common import Metadata
from pywps.response.status import WPS_STATUS

from .utils import default_outputs, model_experiment_ensemble

from .. import runner, util

LOGGER = logging.getLogger("PYWPS")


class StratosphereTroposphere(Process):
    def __init__(self):
        inputs = [
            *model_experiment_ensemble(
                models=['EC-EARTH'],
                experiments=['historical'],
                ensembles=['r2i1p1'],
                start_end_year=(1850, 2005),
                start_end_defaults=(1980, 1989)
            ),
        ]
        outputs = [
            *default_outputs(),
            ComplexOutput('plot_pdf', 'Output plot PDF',
                          abstract='Generated output plot of ESMValTool processing.',
                          as_reference=True,
                          supported_formats=[Format('image/png')]),
            ComplexOutput('plot_reg', 'Output plot REG',
                          abstract='Generated output plot of ESMValTool processing.',
                          as_reference=True,
                          supported_formats=[Format('image/png')]),
            ComplexOutput('plot_ts', 'Output plot TS',
                          abstract='Generated output plot of ESMValTool processing.',
                          as_reference=True,
                          supported_formats=[Format('image/png')]),
            ComplexOutput('archive', 'Archive',
                        abstract='The complete output of the ESMValTool processing as an zip archive.',
                        as_reference=True,
                        supported_formats=[Format('application/zip')]),
        ]

        super(StratosphereTroposphere, self).__init__(
            self._handler,
            identifier="stratosphere-troposphere",
            title="Stratosphere-troposphere coupling and annular modes indices (ZMNAM)",
            version=runner.VERSION,
            abstract="Stratosphere-troposphere coupling and annular modes indices (ZMNAM)",
            metadata=[
                Metadata('ESMValTool', 'http://www.esmvaltool.org/'),
                Metadata('Documentation',
                         'https://copernicus-wps-demo.readthedocs.io/en/latest/processes.html#pydemo',
                         role=util.WPS_ROLE_DOC),
                Metadata('Media',
                         util.diagdata_url() + '/pydemo/pydemo_thumbnail.png',
                         role=util.WPS_ROLE_MEDIA),
                Metadata('ESGF Testdata',
                         'https://esgf1.dkrz.de/thredds/catalog/esgcet/7/cmip5.output1.MPI-M.MPI-ESM-LR.historical.mon.atmos.Amon.r1i1p1.v20120315.html?dataset=cmip5.output1.MPI-M.MPI-ESM-LR.historical.mon.atmos.Amon.r1i1p1.v20120315.ta_Amon_MPI-ESM-LR_historical_r1i1p1_199001-199912.nc'),  # noqa
            ],
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True)

    def _handler(self, request, response):
        response.update_status("starting ...", 0)

        # build esgf search constraints
        constraints = dict(
            model=request.inputs['model'][0].data,
            experiment=request.inputs['experiment'][0].data,
            ensemble=request.inputs['ensemble'][0].data,
        )

        # generate recipe
        response.update_status("generate recipe ...", 10)
        recipe_file, config_file = runner.generate_recipe(
            workdir=self.workdir,
            diag='zmnam',
            constraints=constraints,
            start_year=request.inputs['start_year'][0].data,
            end_year=request.inputs['end_year'][0].data,
            output_format='png',
        )

        # recipe output
        response.outputs['recipe'].output_format = FORMATS.TEXT
        response.outputs['recipe'].file = recipe_file

        # run diag
        response.update_status("running diagnostic ...", 20)
        result = runner.run(recipe_file, config_file)
        logfile = result['logfile']
        plot_dir = result['plot_dir']

        response.outputs['success'].data = result['success']

        # log output
        response.outputs['log'].output_format = FORMATS.TEXT
        response.outputs['log'].file = logfile

        if not result['success']:
            LOGGER.exception('esmvaltool failed!')
            response.update_status("exception occured: " + result['exception'], 100)
            response.status = WPS_STATUS.FAILED
            return response

        # result plot
        response.update_status("collecting output ...", 80)
        response.outputs['plot_pdf'].output_format = Format('application/png')
        response.outputs['plot_pdf'].file = runner.get_output(
            plot_dir,
            path_filter=os.path.join('zmnam', 'main'),
            name_filter="CMIP5*25000Pa_da_pdf",
            output_format="png")

        response.outputs['plot_reg'].output_format = Format('application/png')
        response.outputs['plot_reg'].file = runner.get_output(
            plot_dir,
            path_filter=os.path.join('zmnam', 'main'),
            name_filter="CMIP5*25000Pa_mo_reg",
            output_format="png")

        response.outputs['plot_ts'].output_format = Format('application/png')
        response.outputs['plot_ts'].file = runner.get_output(
            plot_dir,
            path_filter=os.path.join('zmnam', 'main'),
            name_filter="CMIP5*25000Pa_mo_ts",
            output_format="png")

        response.update_status("creating archive of diagnostic result ...", 90)

        response.outputs['archive'].output_format = Format('application/zip')
        response.outputs['archive'].file = runner.compress_output(os.path.join(self.workdir, 'output'), 'diagnostic_result.zip')

        response.update_status("done.", 100)
        return response