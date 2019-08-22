# coding: utf-8

"""
Collection of plot functions.
"""


__all__ = []


import math

import six


class PlotObject(object):

    def __init__(self, fill_func=None, finalize_func=None):
        super(PlotObject, self).__init__()

        self.fill_func = fill_func
        self.finalize_func = finalize_func

    def fill(self, *args, **kwargs):
        return self.fill_func(*args, **kwargs)

    def finalize(self, *args, **kwargs):
        return self.finalize_func(*args, **kwargs)


def rechit_eta_phi_plot(plot_path, rechit_map, eta_map, phi_map, z_map, clusters=None,
        binning=None, z_min=319., z_max=523.):
    import plotlib.root as r
    import ROOT

    r.setup_style()
    canvas, (pad,) = r.routines.create_canvas(pad_props={"RightMargin": 0.17})
    pad.cd()

    # create a dummy histogram for easier plotting
    # and fill one value so that the z-axis is drawn
    binning = binning or (1, 1.4, 3.2, 1, -math.pi / 3., math.pi / 3.)
    dummy_hist = ROOT.TH2F("h", ";#eta;#phi;z / cm", *binning)
    dummy_hist.GetZaxis().SetRangeUser(z_min, z_max)
    r.setup_hist(dummy_hist, pad=pad)
    dummy_hist.Fill(0., 0.)
    dummy_hist.Draw("colz")

    # legend
    n_entries = bool(clusters)
    x, y = r.tools.get_pad_coordinates("l", "t", h_offset=0.015, v_offset=0.02)
    legend = ROOT.TLegend(*r.calculate_legend_coords(n_entries, x1=x, x2=x + 0.14, y2=y))
    r.setup_legend(legend)

    # helper for color-coding z values
    def get_color(z):
        idx = int(math.floor(float(z - z_min) / float(z_max - z_min) * 255))
        return ROOT.TColor.GetColorPalette(idx)

    # create the rechit markers (not as graph to be able to code-code z values)
    rechit_markers = []
    for i, (detid, rechit) in enumerate(six.iteritems(rechit_map)):
        eta = eta_map[detid]
        phi = phi_map[detid]
        if not (binning[1] < eta < binning[2]) or not (binning[4] < phi < binning[5]):
            continue
        marker = ROOT.TMarker(eta, phi, 10)
        color = get_color(z_map[detid])
        r.tools.apply_properties(marker, {"MarkerSize": 0.35, "MarkerColor": color})
        marker.Draw()
        rechit_markers.append(marker)

    # create the simcluster graph when given
    if clusters:
        simcluster_graph = ROOT.TGraph(clusters.size())
        r.setup_graph(simcluster_graph, {"MarkerSize": 1., "MarkerColor": 3, "LineWidth": 0})
        for i, cluster in enumerate(clusters):
            simcluster_graph.SetPoint(i, cluster.simCluster.eta(), cluster.simCluster.phi())
        simcluster_graph.Draw("P")
        legend.AddEntry(simcluster_graph, "SimClusters ({})".format(clusters.size()))
        legend.Draw()

    # cms label
    cms_labels = r.routines.create_cms_labels()
    cms_labels[0].Draw()
    cms_labels[1].Draw()

    # update and save
    r.update_canvas(canvas)
    canvas.SaveAs(plot_path)


def n_rechits_per_cluster_plot(binning=None):
    import plotlib.root as r
    import ROOT

    r.setup_style()
    canvas, (pad,) = r.routines.create_canvas()
    pad.cd()

    # create a histogram for easier plotting
    binning = binning or (25, 0., 500.)
    hist = ROOT.TH1F("h_rechhits_per_cluster", ";Number of RecHits per SimCluster;Entries",
        *binning)
    r.setup_hist(hist, pad=pad)

    def fill(clusters):
        for cluster in clusters:
            hist.Fill(cluster.simCluster.numberOfRecHits())

    def finalize(plot_path):
        pad.cd()

        # cms label
        cms_labels = r.routines.create_cms_labels()

        # draw stuff
        hist.Draw()
        cms_labels[0].Draw()
        cms_labels[1].Draw()

        # update and save
        r.update_canvas(canvas)
        canvas.SaveAs(plot_path)

    return PlotObject(fill, finalize)


def n_rechits_per_cluster_vs_eta_plot(binning=None):
    import plotlib.root as r
    import ROOT

    r.setup_style()
    canvas, (pad,) = r.routines.create_canvas(pad_props={"RightMargin": 0.17})
    pad.cd()

    # create the histogram
    binning = binning or (25, 0., 500., 18, 1.4, 3.2)
    hist = ROOT.TH2F("h_rechhits_per_cluster_vs_eta",
        ";Number of RecHits per SimCluster;#eta;Entries", *binning)
    r.setup_hist(hist, pad=pad)

    def fill(clusters):
        for cluster in clusters:
            hist.Fill(cluster.simCluster.numberOfRecHits(), cluster.simCluster.eta())

    def finalize(plot_path):
        pad.cd()

        # cms label
        cms_labels = r.routines.create_cms_labels()

        # draw stuff
        hist.Draw("colz")
        cms_labels[0].Draw()
        cms_labels[1].Draw()

        # update and save
        r.update_canvas(canvas)
        canvas.SaveAs(plot_path)

    return PlotObject(fill, finalize)
