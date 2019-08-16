# coding: utf-8

"""
Helpful utilities.
"""


__all__ = [
    "cms_run", "parse_cms_run_event", "cms_run_and_publish", "log_runtime", "hadd_task",
    "fwlite_loop",
]


import os
import re
import time
import contextlib

import six
import law


def cms_run(cfg_file, args, yield_output=False):
    if isinstance(args, dict):
        args = list(args.items())

    def cms_run_arg(key, value):
        return " ".join("{}={}".format(key, v) for v in law.util.make_list(value))

    cfg_file = os.path.expandvars(os.path.expanduser(cfg_file))
    args_str = " ".join(cms_run_arg(*tpl) for tpl in args)
    cmd = "cmsRun {} {}".format(cfg_file, args_str)
    fn = law.util.interruptable_popen if not yield_output else law.util.readable_popen
    return fn(cmd, shell=True, executable="/bin/bash")


def parse_cms_run_event(line):
    if not isinstance(line, str):
        return None

    match = re.match(r"^Begin\sprocessing\sthe\s(\d+)\w{2,2}\srecord\..+$", line.strip())
    if not match:
        return None

    return int(match.group(1))


def cms_run_and_publish(task, cfg_file, args, n_events=None):
    # run the command, parse output as it comes
    for obj in cms_run(cfg_file, args, yield_output=True):
        if isinstance(obj, six.string_types):
            print(obj)

            # try to parse the event number
            n_event = parse_cms_run_event(obj)
            if n_event:
                task._publish_message("processing event {}".format(n_event))
                if n_events:
                    task.publish_progress(100. * n_event / n_events)
        else:
            # obj is the popen object
            if obj.returncode != 0:
                raise Exception("cmsRun failed")


@contextlib.contextmanager
def log_runtime(log_fn=None, log_prefix=""):
    t0 = time.time()

    try:
        yield

    finally:
        t1 = time.time()

        if log_fn is None:
            log_fn = six.print_

        msg = "runtime is {}".format(law.util.human_time_diff(seconds=t1 - t0))

        if log_prefix:
            msg = log_prefix + msg

        log_fn(msg)


def hadd_task(task, inputs, output):
    tmp_dir = law.LocalDirectoryTarget(is_tmp=True)
    tmp_dir.touch()

    with task.publish_step("fetching inputs ...", runtime=True):
        def fetch(inp):
            inp.copy_to_local(tmp_dir.child(inp.unique_basename, type="f"), cache=False)
            return inp.unique_basename

        def callback(i):
            task.publish_message("fetch file {} / {}".format(i + 1, len(inputs)))

        bases = law.util.map_verbose(fetch, inputs, every=5, callback=callback)

    with task.publish_step("merging ...", runtime=True):
        with output.localize("w") as tmp_out:
            if len(bases) == 1:
                tmp_out.path = tmp_dir.child(bases[0]).path
            else:
                # merge using hadd
                bases = " ".join(bases)
                cmd = "hadd -n 0 -d {} {} {}".format(tmp_dir.path, tmp_out.path, bases)
                code = law.util.interruptable_popen(cmd, shell=True, executable="/bin/bash",
                    cwd=tmp_dir.path)[0]
                if code != 0:
                    raise Exception("hadd failed")

                task.publish_message("merged file size: {:.2f} {}".format(
                    *law.util.human_bytes(os.stat(tmp_out.path).st_size)))


def fwlite_loop(path, handle_data=None, start=0, end=-1, object_type="Event"):
    """
    Opens one or more ROOT files defined by *path* and yields the FWLite event. When *handle_data*
    is not *None*, it is supposed to be a dictionary ``key -> {"type": ..., "label": ...}``. In that
    case, the handle products are yielded as well in a dictionary, mapped to the key, as
    ``(event, objects dict)``.
    """
    import ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch()
    ROOT.gSystem.Load("libFWCoreFWLite.so")
    ROOT.gSystem.Load("libDataFormatsFWLite.so")
    ROOT.FWLiteEnabler.enable()
    from DataFormats.FWLite import Events, Runs, Handle

    paths = path if isinstance(path, (list, tuple)) else [path]

    handles = {}
    if handle_data:
        for key, data in handle_data.items():
            handles[key] = Handle(data["type"])

    objects = locals()[object_type + "s"](paths)
    if start > 0:
        objects.to(start)

    for i, obj in enumerate(objects):
        if end >= 0 and (start + i) >= end:
            break

        if handle_data:
            products = {}
            for key, data in handle_data.items():
                obj.getByLabel(data["label"], handles[key])
                products[key] = handles[key].product()
            yield obj, products
        else:
            yield obj
