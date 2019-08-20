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
        import plotlib.root as r
        import ROOT

        output_collection = self.output()
        output_collection.dir.touch()

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

        # setup canvas and pad
        r.setup_style()
        canvas, (pad,) = r.routines.create_canvas()
        pad.cd()

        for i, (event, data) in enumerate(fwlite_loop(input_path, handle_data)):
            print("event {}".format(i))

            rec_hit_map = {}
            for src in ["recHitsEE", "recHitsHEF", "recHitsHEB"]:
                collection = data[src]
                for rec_hit in collection:
                    rec_hit_map[rec_hit.detid()] = rec_hit

            clusters = data["extendedSimClusters"]
            eta_map = data["recHitEta"]
            phi_map = data["recHitPhi"]

            # create an eta-phi plot
            binning = (1, 1.5, 3.5, 1, -math.pi / 3., math.pi / 3.)
            dummy_hist = ROOT.TH2F("h", ";#eta;#phi;Entries", *binning)
            rechit_graph = ROOT.TGraph(len(rec_hit_map))

            for i, (det_id, rec_hit) in enumerate(six.iteritems(rec_hit_map)):
                eta = eta_map[det_id]
                phi = phi_map[det_id]
                rechit_graph.SetPoint(i, eta, phi)

            r.setup_hist(dummy_hist, pad=pad)
            r.setup_graph(rechit_graph, {"MarkerSize": 0.25, "MarkerColor": 2})

            dummy_hist.Draw()
            rechit_graph.Draw("P")

            r.update_canvas(canvas)
            canvas.SaveAs(output_collection.dir.child("rechits_eta_phi_0.png", type="f").path)

            # print("first rechit energy: {}".format(recHitsEE[0].energy()))
            # print("first rechit detid: {}".format(recHitsEE[0].detid()))
            # print("first rechit eta: {}".format(etaMap[recHitsEE[0].detid()]))
            # print("first rechit phi: {}".format(phiMap[recHitsEE[0].detid()]))

            # print("radius of esc 0: {}".format(clusters[0].showerRadius))
            # print("energy of esc 0: {}".format(clusters[0].simCluster.energy()))

            break
