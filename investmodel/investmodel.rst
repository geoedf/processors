InVESTModel
====================

.. py:class:: GeoEDF.processor.InVESTModel()

   Processor for executing any InVEST model using the model API.
    An InVEST model requires additional parameters to run.  These parameters
    may be provided as either:
        * a mapping of arguments (under the "args" key)
        * a path to a datastack archive or parameter set (under the "datastack"
            key).  This may be hosted on a remote server, accessible via
            http(s).
    The model name must always be provided, where the model name matches those
    model names defined in ``natcap.invest.model_metadata``.

   .. py:attribute:: model (str,required)

   The path to the model is to be specified. 

   .. py:attribute:: datastack (str,optional)
    
   If the datastack starts with http it will be fetched from the website specified. Otherwise the path must be specified.

   .. py:attribute:: args (list,optional)

   Instead of a datastack, the user can provide a set of arguments. 
