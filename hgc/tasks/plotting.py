# coding: utf-8

"""
Plotting tasks.
"""


__all__ = ["PlotTask"]


import math

import law
import luigi
import six

from hgc.tasks.base import Task
from hgc.tasks.simulation import GeneratorParameters, RecoTask
from hgc.util import fwlite_loop
import hgc.plots.plots as plots


luigi.namespace("plot", scope=__name__)


class ESCPlots(GeneratorParameters):
    """
    Produced plots:
      - Number of RecHits per ExtendedSimCluster (maybe also vs. energy, pileup, id, etc.)
      - Number of SimClusters vs. Egun (mostly important for electrons when shot from 0|0|0)
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
            # self.local_target("showerRadius.png", store="$HGC_STORE"),
            self.local_target("rechits_eta_phi_0.png", store="$HGC_STORE"),
        ])

    @law.decorator.notify
    def run(self):
        output_collection = self.output()
        output_collection.dir.touch()
        plot_path = lambda name: output_collection.dir.child(name, type="f").path

        input_path = self.input()["reco"].path
        handle_data = {
            "extendedSimClusters": {
                "type": "std::vector<ticl::ExtendedSimCluster>",
                "label": ("extendedSimClusters", "", "RECO"),
            },
            "recHitsEE": {
                "type": "edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit> >",
                "label": ("HGCalRecHit", "HGCEERecHits", "RECO"),
            },
            "recHitsHEF": {
                "type": "edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit> >",
                "label": ("HGCalRecHit", "HGCHEFRecHits", "RECO"),
            },
            "recHitsHEB": {
                "type": "edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit> >",
                "label": ("HGCalRecHit", "HGCHEBRecHits", "RECO"),
            },
            "recHitEta": {
                "type": "std::map<DetId, float>",
                "label": ("extendedSimClusters", "recHitEta", "RECO"),
            },
            "recHitPhi": {
                "type": "std::map<DetId, float>",
                "label": ("extendedSimClusters", "recHitPhi", "RECO"),
            },
        }

        for i, (event, objects) in enumerate(fwlite_loop(input_path, handle_data)):
            print("event {}".format(i))

            # get objects
            clusters = objects["extendedSimClusters"]
            eta_map = objects["recHitEta"]
            phi_map = objects["recHitPhi"]

            # fill the rechit map
            rechit_map = {}
            for src in ["recHitsEE", "recHitsHEF", "recHitsHEB"]:
                collection = objects[src]
                for rechit in collection:
                    rechit_map[rechit.detid()] = rechit

            # create an eta-phi plot of the first event
            if i == 0:
                plots.rechit_eta_phi_plot(plot_path("rechits_eta_phi_{}.png".format(i)), rechit_map,
                    eta_map, phi_map, clusters)

            # print("first rechit energy: {}".format(recHitsEE[0].energy()))
            # print("first rechit detid: {}".format(recHitsEE[0].detid()))
            # print("first rechit eta: {}".format(etaMap[recHitsEE[0].detid()]))
            # print("first rechit phi: {}".format(phiMap[recHitsEE[0].detid()]))

            # print("radius of esc 0: {}".format(clusters[0].showerRadius))
            # print("energy of esc 0: {}".format(clusters[0].simCluster.energy()))

            break
