# coding: utf-8

"""
Collection of plot functions.
"""


__all__ = ["rechit_eta_phi_plot"]


import math

import six


def rechit_eta_phi_plot(plot_path, rechit_map, eta_map, phi_map, clusters=None, binning=None):
    import plotlib.root as r
    import ROOT

    r.setup_style()
    canvas, (pad,) = r.routines.create_canvas()
    pad.cd()

    # create a dummy histogram for easier plotting
    binning = binning or (1, 1.3, 3.3, 1, -math.pi / 3., math.pi / 3.)
    dummy_hist = ROOT.TH2F("h", ";#eta;#phi;Entries", *binning)
    r.setup_hist(dummy_hist, pad=pad)
    dummy_hist.Draw()

    # legend
    n_entries = 1 + bool(clusters)
    x, y = r.tools.get_pad_coordinates("l", "t", h_offset=0.015, v_offset=0.02)
    legend = ROOT.TLegend(*r.calculate_legend_coords(n_entries, x1=x, x2=x + 0.14, y2=y))
    r.setup_legend(legend)

    # create the rechit graph
    rechit_graph = ROOT.TGraph(len(rechit_map))
    r.setup_graph(rechit_graph, {"MarkerSize": 0.25, "MarkerColor": 2, "LineWidth": 0})
    for i, (detid, rechit) in enumerate(six.iteritems(rechit_map)):
        eta = eta_map[detid]
        phi = phi_map[detid]
        rechit_graph.SetPoint(i, eta, phi)
    rechit_graph.Draw("P")
    legend.AddEntry(rechit_graph, "RecHits")

    # create the simcluster graph when given
    if clusters:
        simcluster_graph = ROOT.TGraph(clusters.size())
        r.setup_graph(simcluster_graph, {"MarkerSize": 1., "MarkerColor": 3, "LineWidth": 0})
        for i, cluster in enumerate(clusters):
            simcluster_graph.SetPoint(i, cluster.simCluster.eta(), cluster.simCluster.phi())
        simcluster_graph.Draw("P")
        legend.AddEntry(simcluster_graph, "SimClusters")

    # cms label
    cms_labels = r.routines.create_cms_labels()

    # draw stuff
    legend.Draw()
    cms_labels[0].Draw()
    cms_labels[1].Draw()

    # update and save
    r.update_canvas(canvas)
    canvas.SaveAs(plot_path)
