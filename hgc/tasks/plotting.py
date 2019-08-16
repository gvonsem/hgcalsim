# coding: utf-8

"""
Plotting tasks.
"""

__all__ = ["PlotTask"]


import law
import luigi

from hgc.tasks.base import Task
from hgc.tasks.simulation import GeneratorParameters, RecoTask
from hgc.util import fwlite_loop

luigi.namespace("plot", scope=__name__)


# class PlotTask(Task):

#     n_events = NtupTask.n_events

#     def requires(self):
#         return NtupTask.req(self, n_tasks=1)

#     def output(self):
#         return law.SiblingFileCollection([
#             self.local_target("eta_phi_{}.png".format(i))
#             for i in range(self.n_events)
#         ])

#     @law.decorator.notify
#     def run(self):
#         from hgc.plots.plots import particle_rechit_eta_phi_plot

#         # ensure that the output directory exists
#         output = self.output()
#         output.dir.touch()

#         # load the data to a structured numpy array
#         input_target = self.input()["collection"][0]
#         data = input_target.load(formatter="root_numpy", treename="ana/hgc")

#         for i, event in enumerate(data):
#             with output[i].localize("w") as tmp_out:
#                 particle_rechit_eta_phi_plot(event, "gunparticle", tmp_out.path)


class ESCPlots(GeneratorParameters):
    """
    Produced plots:
      - Number of RecHits per ExtendedSimCluster (maybe also vs. energy, pileup, id, etc.)
      - Energy profiles per ESC: a) energy vs. R, b) cumulative energy vs. R
      - R68 vs. energy, pileup, id, etc.
      - Axis direction vs. default SC direction
      - For >= 2 ESCs:
        - M vs. Rgun
        - M vs. Fraction of shared RecHits (2D)
    """

    def requires(self):
        return RecoTask.req(self, n_tasks=1, branch=0)

    def output(self):
        return law.SiblingFileCollection([
            self.local_target("showerRadius.png"),
        ])

    @law.decorator.notify
    @law.decorator.localize
    def run(self):
        input_path = self.input()["reco"].path
        handle_data = {
            "escs": {
                "type": "std::vector<ticl::ExtendedSimCluster>",
                "label": ("extendedSimClusters", "", "RECO"),
            },
        }
        for i, (event, data) in enumerate(fwlite_loop(input_path, handle_data)):
            print("event {}".format(i))

            escs = data["escs"]
            print("radius of esc 0: {}".format(escs[0].showerRadius))
