import os

from pywps import Process
from pywps import LiteralInput, LiteralOutput
from pywps import ComplexInput, ComplexOutput
from pywps import Format, FORMATS
from pywps.app.Common import Metadata

from copernicus import runner
from copernicus import util

import logging
LOGGER = logging.getLogger("PYWPS")


class RainFarm(Process):
    def __init__(self):
        inputs = [
            LiteralInput('model', 'Model',
                         abstract='Choose a model like MPI-ESM-LR.',
                         data_type='string',
                         allowed_values=['ACCESS1-0', ],
                         default='ACCESS1-0'),
            LiteralInput('experiment', 'Experiment',
                         abstract='Choose an experiment like historical.',
                         data_type='string',
                         allowed_values=['historical', ],
                         default='historical'),
            LiteralInput('start_year', 'Start year', data_type='integer',
                         abstract='Start year of model data.',
                         default="1997"),
            LiteralInput('end_year', 'End year', data_type='integer',
                         abstract='End year of model data.',
                         default="1997"),
            LiteralInput('subset', 'Geographical subset',
                         abstract='Choose a geographical subset with a Bounding Box: 4,13,44,53',
                         data_type='string',
                         default='4,13,44,53'),
            LiteralInput('regridding', 'Regridding',
                         abstract='Flag for regridding.',
                         data_type='boolean',
                         default='0'),
            LiteralInput('slope', 'Slope',
                         abstract='Flag for slope.',
                         data_type='boolean',
                         default='0'),
            LiteralInput('num_ens_members', 'Number of ensemble members',
                         abstract='Choose a number of ensemble members.',
                         data_type='integer',
                         default='2'),
            LiteralInput('num_subdivs', 'Number of subdivisions',
                         abstract='Choose a number of subdivisions.',
                         data_type='integer',
                         default='8'),
        ]
        outputs = [
            ComplexOutput('output', 'Output plot',
                          abstract='Generated output plot of ESMValTool processing.',
                          as_reference=True,
                          supported_formats=[Format('image/png')]),
        ]

        super(RainFarm, self).__init__(
            self._handler,
            identifier="rainfarm",
            title="RainFARM stochastic downscaling",
            version=runner.VERSION,
            abstract="Tool to perform stochastic precipitation downscaling, generating an ensemble of fine-scale "
            " precipitation fields from information simulated by climate models at regional scale.",
            metadata=[
                Metadata('ESMValTool', 'http://www.esmvaltool.org/'),
                Metadata('Documentation',
                         'https://copernicus-wps-demo.readthedocs.io/en/latest/processes.html#rainfarm',
                         role=util.WPS_ROLE_DOC),
                Metadata('Media',
                         util.diagdata_url() + '/rainfarm/rainfarm_thumbnail.png',
                         role=util.WPS_ROLE_MEDIA),
                Metadata('Diagnostic Description',
                         util.diagdata_url() + '/rainfarm/description.md',
                         role=util.MAGIC_ROLE_DOC),
                Metadata('Diagnostic Metadata',
                         util.diagdata_url() + '/rainfarm/rainfarm.yml',
                         role=util.MAGIC_ROLE_METADATA),
            ],
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True)

    def _handler(self, request, response):
        response.update_status("starting ...", 0)
        # run diag
        response.update_status("running diag ...", 20)
        # result plot
        response.update_status("collect output plot ...", 90)
        response.outputs['output'].output_format = Format('image/png')
        response.outputs['output'].file = util.diagdata_file(os.path.join('rainfarm', 'RainFARM_example_64x64.png'))
        response.update_status("done.", 100)
        return response
