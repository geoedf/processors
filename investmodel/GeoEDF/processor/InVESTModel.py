#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contextlib
import importlib
import logging
import os
import shutil
import warnings
import zipfile

from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError
from natcap.invest import datastack
from natcap.invest import utils
from natcap.invest.model_metadata import MODEL_METADATA

LOGGER = logging.getLogger(logging.INFO)


@contextlib.contextmanager
def _set_temp_env_vars(workspace):
    workspace = os.path.abspath(workspace)
    old_variable_values = {}
    for variable in ('TMPDIR', 'TEMP', 'TMP'):
        try:
            old_variable_values[variable] = os.environ[variable]
        except KeyError:
            pass
        os.environ[variable] = workspace

    yield

    for varname, old_value in old_variable_values.items():
        if os.environ[varname] != workspace:
            warnings.warn(
                f"Environment variable {varname} changed value during "
                "execution of an InVEST model; overwriting.")
        os.environ[varname] = old_value


class InVESTModel(GeoEDFPlugin):
    """ Module for executing any InVEST model using the model API entrypoints
    """

    __optional_params = []
    __required_params = ['model', 'model_input']

    # we use just kwargs since this makes it easier to instantiate the object
    # from the GeoEDFProcessor class
    def __init__(self, **kwargs):

        # list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError(
                    f'Required parameter {param} for InVESTModel '
                    'not provided')

        # set all required parameters
        for key in self.__required_params:
            setattr(self, key, kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self, key, kwargs.get(key, None))

        self.kwargs = kwargs

        super().__init__()

    # the process method that executes the specific InVEST model with a
    # dictionary of args constructed from kwargs
    def process(self):

        # construct args from kwargs by deleting the required and optional
        # params
        for arg in self.provided_params:
            self.kwargs.pop(arg)

        # assume for now that input is always a zip file
        # copy file to processor output dir and then unzip
        shutil.copy(self.model_input, self.target_path)

        # determine input filename
        model_input_filename = os.path.split(self.model_input)[1]
        zipfile_path = os.path.join(self.targeT_path, model_input_filename)
        with zipfile.ZipFile(zipfile_path, 'r') as zip_ref:
            zip_ref.extractall(self.target_path)

        # delete zip file
        os.remove(zipfile_path)

        # model dirname
        model_dirname = os.path.splitext(model_input_filename)[0]

        # chdir to right path
        os.chdir(os.path.join(self.target_path, model_dirname))

        # workspace_dir
        workspace = os.getcwd()
        self.kwargs['workspace_dir'] = workspace

        # use importlib to import the necessary model
        model_mname = MODEL_METADATA[self.model].pyname
        model_module = importlib.import_module(model_mname)

        # prepare_workspace will:
        #  * capture GDAL logging
        #  * write to a named, timestamped logfile in the workspace
        #  * create a new temp directory within the workspace
        with utils.prepare_workspace(
                workspace, MODEL_METADATA[self.model].model_title,
                logging_level=logging.INFO):
            with _set_temp_env_vars(workspace):
                model_module.execute(self.kwargs)

        # zip up folder again to return
        source_dir = os.path.join(self.target_path, model_dirname)
        shutil.make_archive(
            f'{source_dir}.zip', 'zip', source_dir)
