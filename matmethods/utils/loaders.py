# coding: utf-8
# Copyright (c) Materials Virtual Lab.
# Distributed under the terms of the BSD License.

from __future__ import division, unicode_literals, print_function

"""
#TODO: Replace with proper module doc.
"""


from monty.json import MontyDecoder
from fireworks import Workflow, LaunchPad
from matmethods.vasp.vasp_powerups import decorate_write_name


def get_wf_from_spec_dict(structure, wfspec):
    """
    Load a WF from a structure and a spec dict. This allows simple
    custom workflows to be constructed quickly via a YAML file.

    Args:
        structure (Structure): An input structure object.
        wfspec (dict): A dict specifying workflow. A sample of the dict in
            YAML format for the usual MP workflow is given as follows:

            ```
            fireworks:
            - fw: matmethods.vasp.fws.OptimizeFW
            - fw: matmethods.vasp.fws.StaticFW
              params:
                parents: 0
            - fw: matmethods.vasp.fws.NonSCFUniformFW
              params:
                parents: 1
            - fw: matmethods.vasp.fws.NonSCFLineFW
              params:
                parents: 1
            common_params:
              db_file: db.json
              vasp_cmd: /opt/vasp
            ```

            The `fireworks` key is a list of fireworks. Each firework is
            specified via "fw": <explicit path>, and all parameters other than
            structure are specified via `params` which is a dict. `parents` is
            a special parameter, which provides the *indices* of the parents
            of that particular firework in the list.

            `common_params` specify a common set of parameters that are
            passed to all fireworks, e.g., db settings.

    Returns:
        Workflow
    """
    fws = []
    common_params = wfspec.get("common_params", {})
    for d in wfspec["fireworks"]:
        modname, classname = d["fw"].rsplit(".", 1)
        mod = __import__(modname, globals(), locals(), [classname], 0)
        if hasattr(mod, classname):
            cls_ = getattr(mod, classname)
            params = {k: MontyDecoder().process_decoded(v) for k, v in d.get("params", {}).items()}
            params.update(common_params)
            if "parents" in params:
                params["parents"] = fws[params["parents"]]
            fws.append(cls_(structure, **params))
    return Workflow(fws, name=structure.composition.reduced_formula)


def add_to_lpad(workflow, decorate=False):
    """
    Add the workflow to the launchpad

    Args:
        workflow (Workflow): workflow for db insertion
        decorate (bool): If set an empty file with the name
            "FW--<fw.name>" will be written to the launch directory
    """
    lp = LaunchPad.auto_load()
    workflow = decorate_write_name(workflow) if decorate else workflow
    lp.add_wf(workflow)