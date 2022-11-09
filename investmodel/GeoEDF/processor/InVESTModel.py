#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contextlib
import importlib
import logging
import os
import shutil
import unittest
import warnings

import requests
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError
from natcap.invest import datastack
from natcap.invest import utils
from natcap.invest.model_metadata import MODEL_METADATA

logging.getLogger().addHandler(logging.NullHandler)  # avoid no-handler warning
LOGGER = logging.getLogger(__name__)
VALID_MODEL_NAMES = sorted(MODEL_METADATA.keys())


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
    """Processor for executing any InVEST model using the model API.

    An InVEST model requires additional parameters to run.  These parameters
    may be provided as either:

        * a mapping of arguments (under the "args" key)
        * a path to a datastack archive or parameter set (under the "datastack"
            key).  This may be hosted on a remote server, accessible via
            http(s).

    The model name must always be provided, where the model name matches those
    model names defined in ``natcap.invest.model_metadata``.
    """

    __optional_params = ['datastack', 'args']
    __required_params = ['model']

    # we use just kwargs since this makes it easier to instantiate the object
    # from the GeoEDFProcessor class
    def __init__(self, **kwargs):
        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError(
                    f'Required parameter {param} for InVESTModel '
                    'not provided.')

        if kwargs['model'] not in VALID_MODEL_NAMES:
            raise GeoEDFError(
                f"Model name invalid; must be one of {VALID_MODEL_NAMES}")

        if (set(self.__optional_params).issubset(set(kwargs.keys())) or not
                set(self.__optional_params).intersection(set(kwargs.keys()))):
            raise GeoEDFError(
                "Either 'datastack' or 'args' must be defined, but not both")

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
        if self.datastack:
            # download the datastack if it's remote.
            if self.datastack.startswith('http'):
                local_datastack = os.path.join(
                    self.target_path, 'datastack.tar.gz')
                r = requests.get(
                    self.datastack, allow_redirects=True, stream=True)
                with open(local_datastack, 'wb') as file:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)

            # If the datastack is somewhere on the local filesystem but not in
            # the target directory, copy it into the target directory.
            elif os.path.commonprefix(
                    [self.target_path, self.datastack]) != self.target_path:
                shutil.copy(self.datastack, self.target_path)
                local_datastack = os.path.join(
                    self.target_path, os.path.basename(self.datastack))

            # Otherwise, the local datastack should already be in the target
            # directory.
            else:
                local_datastack = self.datastack

            # Figure out which type of datastack the user provided.
            ds_type, _ = datastack.get_datastack_info(local_datastack)

            # Unzip a tar.gz archive if the datastack is an archive.
            if ds_type == 'archive':
                ds_info = datastack.extract_datastack_archive(
                    local_datastack, self.target_path)
                os.remove(local_datastack)
                model_args = ds_info.args

            # Assume the user provided a datastack parameter set instead, which
            # can just be loaded directly.
            else:
                ds_info = datastack.extract_parameter_set(local_datastack)
                model_args = ds_info.args

        # If the user didn't provide a datastack, they provided a direct
        # dictionary of arguments, so use them verbatim.
        else:
            model_args = self.args

        # workspace_dir
        workspace = os.getcwd()
        self.kwargs['workspace_dir'] = workspace

        # use importlib to import the necessary model
        model_mname = MODEL_METADATA[self.model].pyname
        model_module = importlib.import_module(model_mname)

        # Validate the user's defined inputs
        validation_warnings = model_module.validate(model_args)
        if validation_warnings:
            raise GeoEDFError(
                f"Model inputs failed validation: {validation_warnings}")

        # prepare_workspace will:
        #  * capture GDAL logging
        #  * write to a named, timestamped logfile in the workspace
        #  * create a new temp directory within the workspace
        with utils.prepare_workspace(
                workspace, MODEL_METADATA[self.model].model_title,
                logging_level=logging.INFO):
            with _set_temp_env_vars(workspace):
                model_module.execute(model_args)

        # zip up folder again to return
        shutil.make_archive(
            'workspace.zip', 'zip', workspace)


class InVESTProcessorTests(unittest.TestCase):
    def test_invalid_name(self):
        """Test that an invalid model name raises GeoEDFError."""
        with self.assertRaises(GeoEDFError):
            plugin = InVESTModel(model='bad model name')
