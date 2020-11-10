import matplotlib.pyplot as plt
import numpy as np

from django.http import HttpResponse, Http404

import matplotlib.path as mpath
import matplotlib.patches as mpatches

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

import mpld3
from mpld3 import plugins, utils
import redis

r = redis.Redis(host = 'meep_celery', port = 6379, db=0)

class DragPlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", DragPlugin);
    DragPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    DragPlugin.prototype.constructor = DragPlugin;
    DragPlugin.prototype.requiredProps = ["id"];
    DragPlugin.prototype.defaultProps = {}
    function DragPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
        mpld3.insert_css("#" + fig.figid + " path.dragging",
                         {"fill-opacity": "1.0 !important",
                          "stroke-opacity": "1.0 !important"});
    };

    DragPlugin.prototype.draw = function(){
        var obj = mpld3.get_element(this.props.id);

        var drag = d3.drag()
            .subject(function(d) { return {x:obj.ax.x(d[0]),
                                          y:obj.ax.y(d[1])}; })
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);

        obj.elements()
           .data(obj.offsets)
           .style("cursor", "default")
           .call(drag);

        function dragstarted(d) {
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
          d[0] = obj.ax.x.invert(d3.event.x);
          d[1] = obj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
        }

        function dragended(d) {
          d3.select(this).classed("dragging", false);
        }
    }
    """

    def __init__(self, points):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "id": utils.get_id(points, suffix)}


class LinkedDragPlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", DragPlugin);
    DragPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    DragPlugin.prototype.constructor = DragPlugin;
    DragPlugin.prototype.requiredProps = ["idpts", "idline", "idpatch"];
    DragPlugin.prototype.defaultProps = {}
    function DragPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    DragPlugin.prototype.draw = function(){
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        var lineobj = mpld3.get_element(this.props.idline, this.fig);

        var drag = d3.drag()
            .subject(function(d) { return {x:ptsobj.ax.x(d[0]),
                                          y:ptsobj.ax.y(d[1])}; })
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);

        lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));
        patchobj.path.attr("d", patchobj.datafunc(ptsobj.offsets,
                                                  patchobj.pathcodes));
        lineobj.data = ptsobj.offsets;
        patchobj.data = ptsobj.offsets;

        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);

        function dragstarted(d) {
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));
          patchobj.path.attr("d", patchobj.datafunc(ptsobj.offsets,
                                                    patchobj.pathcodes));
        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);
        }
    }

    mpld3.register_plugin("drag", DragPlugin);
    """

    def __init__(self, points, line, patch):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "idpatch": utils.get_id(patch)}

class SliderView(mpld3.plugins.PluginBase):
    """ Add slider and JavaScript / Python interaction. """

    JAVASCRIPT = """
    mpld3.register_plugin("sliderview", SliderViewPlugin);
    SliderViewPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    SliderViewPlugin.prototype.constructor = SliderViewPlugin;
    SliderViewPlugin.prototype.requiredProps = ["idline", "callback_func"];
    SliderViewPlugin.prototype.defaultProps = {}

    function SliderViewPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    SliderViewPlugin.prototype.draw = function(){
      var line = mpld3.get_element(this.props.idline);
      var callback_func = this.props.callback_func;

      var div = d3.select("#" + this.fig.figid);

      // Create slider
      div.append("input").attr("type", "range").attr("min", 0).attr("max", 10).attr("step", 0.1).attr("value", 1)
          .on("change", function() {
              var command = callback_func + "(" + this.value + ")";
              console.log("running "+command);
              var callbacks = { 'iopub' : {'output' : handle_output}};
              var kernel = IPython.notebook.kernel;
              kernel.execute(command, callbacks, {silent:false});
          });

      function handle_output(out){
        //console.log(out);
        var res = null;
        // if output is a print statement
        if (out.msg_type == "stream"){
          res = out.content.data;
        }
        // if output is a python object
        else if(out.msg_type === "pyout"){
          res = out.content.data["text/plain"];
        }
        // if output is a python error
        else if(out.msg_type == "pyerr"){
          res = out.content.ename + ": " + out.content.evalue;
          alert(res);
        }
        // if output is something we haven't thought of
        else{
          res = "[out type not implemented]";  
        }

        // Update line data
        line.data = JSON.parse(res);
        line.elements()
          .attr("d", line.datafunc(line.data))
          .style("stroke", "black");

       }

    };
    """

    def __init__(self, line, callback_func):
        self.dict_ = {"type": "sliderview",
                      "idline": mpld3.utils.get_id(line),
                      "callback_func": callback_func}

def patchPath(request):
    fig, ax = plt.subplots()

    Path = mpath.Path
    path_data = [
        (Path.MOVETO, (1.58, -2.57)),
        (Path.CURVE4, (0.35, -1.1)),
        (Path.CURVE4, (-1.75, 2.0)),
        (Path.CURVE4, (0.375, 2.0)),
        (Path.LINETO, (0.85, 1.15)),
        (Path.CURVE4, (2.2, 3.2)),
        (Path.CURVE4, (3, 0.05)),
        (Path.CURVE4, (2.0, -0.5)),
        (Path.CLOSEPOLY, (1.58, -2.57)),
        ]
    codes, verts = zip(*path_data)
    path = mpath.Path(verts, codes)
    patch = mpatches.PathPatch(path, facecolor='r', alpha=0.5)
    ax.add_patch(patch)

    # plot control points and connecting lines
    x, y = zip(*path.vertices[:-1])
    points = ax.plot(x, y, 'go', ms=10)
    line = ax.plot(x, y, '-k')

    ax.grid(True, color='gray', alpha=0.5)
    ax.axis('equal')
    ax.set_title("Drag Points to Change Path", fontsize=18)

    plugins.connect(fig, LinkedDragPlugin(points[0], line[0], patch))

    plot_string = mpld3.fig_to_html(fig, d3_url=None, mpld3_url=None, no_extras=False, template_type='general', figid=None, use_http=False)

    return HttpResponse(plot_string, status=200)



def plot(request, title):
    fig = plt.figure(figsize=(4,4))
    ax = plt.gca()
    if title == None:
        x = np.linspace(-2, 2, 20)
        y = x[:, None]
        X = np.zeros((20, 20, 4))

        X[:, :, 0] = np.exp(- (x - 1) ** 2 - (y) ** 2)
        X[:, :, 1] = np.exp(- (x + 0.71) ** 2 - (y - 0.71) ** 2)
        X[:, :, 2] = np.exp(- (x + 0.71) ** 2 - (y + 0.71) ** 2)
        X[:, :, 3] = np.exp(-0.25 * (x ** 2 + y ** 2))

        im = ax.imshow(X, extent=(10, 20, 10, 20),
                    origin='lower', zorder=1, interpolation='nearest')
        fig.colorbar(im, ax=ax)

        ax.set_title('An Image', size=20)

        plugins.connect(fig, plugins.MousePosition(fontsize=14))

        plot_string = mpld3.fig_to_html(fig, d3_url=None, mpld3_url=None, no_extras=False, template_type='general', figid=None, use_http=False)

        return HttpResponse(plot_string, status=200)
    else:
        plot_string = r.get('user_' + str(0) + '_plot_' + title)

        return HttpResponse(plot_string, status=200)


        
def struct_editor(request):
    fig = plt.figure(figsize=(5,5))
    ax = plt.gca()

    np.random.seed(0)
    points = ax.plot(np.random.normal(size=20),
                    np.random.normal(size=20), 'or', alpha=0.5,
                    markersize=50, markeredgewidth=1)
    ax.set_title("Click and Drag", fontsize=18)

    plugins.connect(fig, DragPlugin(points[0]))

    plot_string = mpld3.fig_to_html(fig, d3_url=None, mpld3_url=None, no_extras=False, template_type='general', figid=None, use_http=False)

    return HttpResponse(plot_string, status=200)


def matrix_editor(request):
    fig = plt.figure(figsize=(5,5))
    ax = plt.gca()

    np.random.seed(0)
    points = ax.plot(np.random.normal(size=20),
                    np.random.normal(size=20), 'or', alpha=0.5,
                    markersize=50, markeredgewidth=1)
    ax.set_title("Matrix visualizer", fontsize=18)

    # plugins.connect(fig, DragPlugin(points[0]))

    plot_string = mpld3.fig_to_html(fig, d3_url=None, mpld3_url=None, no_extras=False, template_type='general', figid=None, use_http=False)

    return HttpResponse(plot_string, status=200)