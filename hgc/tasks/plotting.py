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
        return RecoTask.req(self, n_tasks=1, branch=0, _prefer_cli=["version", "nevts"])

    def output(self):
        return law.SiblingFileCollection(law.util.flatten(
            # rechit eta-phi plot for the first 5 events
            [
                self.local_target("rechits_eta_phi_{}.png".format(i), store="$HGC_STORE")
                for i in range(min(5, self.nevts))
            ],
            # the number of rechits per simcluster
            self.local_target("rechits_per_simcluster.png", store="$HGC_STORE"),
            # the number of rechits per simcluster vs. simcluster eta
            self.local_target("rechits_per_simcluster_vs_eta.png", store="$HGC_STORE"),
        ))

    @law.decorator.notify
    def run(self):
        # ensure the output directory exists and create a helper to find the path of plots to save
        output_collection = self.output()
        output_collection.dir.touch()
        plot_path = lambda name: output_collection.dir.child(name, type="f").path

        # progress callback
        publish_progress = self.create_progress_callback(self.nevts)
        def progress(i):
            publish_progress(i)
            if i % 10 == 0:
                self.publish_message("event {}".format(i))

        # get the input path and define the objects to read
        input_path = self.input()["reco"].path
        handle_data = {
            "extendedSimClusters": {
                "type": "std::vector<ticl::ExtendedSimCluster>",
                "label": ("extendedSimClusters", "", "RECO"),
            },
            "recHitsEE": {
                "type": "edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit>>",
                "label": ("HGCalRecHit", "HGCEERecHits", "RECO"),
            },
            "recHitsHEF": {
                "type": "edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit>>",
                "label": ("HGCalRecHit", "HGCHEFRecHits", "RECO"),
            },
            "recHitsHEB": {
                "type": "edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit>>",
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
            "recHitZ": {
                "type": "std::map<DetId, float>",
                "label": ("extendedSimClusters", "recHitZ", "RECO"),
            },
        }

        # register plots that consider all events
        n_rechits_per_cluster_plot = plots.n_rechits_per_cluster_plot()
        n_rechits_per_cluster_vs_eta_plot = plots.n_rechits_per_cluster_vs_eta_plot()

        # fwlite loop
        for i, (event, objects) in enumerate(fwlite_loop(input_path, handle_data, end=self.nevts)):
            progress(i)

            clusters = objects["extendedSimClusters"]

            if i < 5:
                eta_map = objects["recHitEta"]
                phi_map = objects["recHitPhi"]
                z_map = objects["recHitZ"]

                rechit_map = {}
                for src in ["recHitsEE", "recHitsHEF", "recHitsHEB"]:
                    collection = objects[src]
                    for rechit in collection:
                        rechit_map[rechit.detid()] = rechit

                plots.rechit_eta_phi_plot(plot_path("rechits_eta_phi_{}.png".format(i)), rechit_map,
                    eta_map, phi_map, z_map, clusters)

            n_rechits_per_cluster_plot.fill(clusters)
            n_rechits_per_cluster_vs_eta_plot.fill(clusters)

        n_rechits_per_cluster_plot.finalize(plot_path("rechits_per_simcluster.png"))
        n_rechits_per_cluster_vs_eta_plot.finalize(plot_path("rechits_per_simcluster_vs_eta.png"))
