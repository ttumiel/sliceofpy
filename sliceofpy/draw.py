import numpy as np
from mecode import G as meG

# Monkey-patch mecode so that I can draw the slicers in 2-D and 3-D?

# Save non-rapid movements for display in 2d and 3d
# create method for showing the full movements (meG.view())
class G():
    """
    A wrapper class for mecode.G that adds better plotting functionality.
    """
    def __init__(self, vertices, *args, **kwargs):
        self.g = meG(*args, **kwargs)
        self.g.absolute()

        self.layer_height = kwargs['layer_height']
        self.stored_fast = None
        self.X, self.Y, self.Z = (0,0,0)
        self.continuous_extrusions = []
        self.tmp_cnt = [] # Store all of the contour pts in a continuous contour
        self.tmp_layer = [] # Stores all the contours of a particular layer
        self.layer_slices = [] # Stores all the contours of all layers (ascending)

        self.vertices = vertices
        self.x_min,self.y_min,self.z_min = vertices.min(axis=0)
        self.x_max,self.y_max,self.z_max = vertices.max(axis=0)

    def __enter__(self):
        self.g.__enter__()
        return self

    def __exit__(self, *args):
        self.g.__exit__(*args)

    def move(self, x=None, y=None, z=None, rapid=False, **kwargs):
        if self.Z != z:
            self.check_tmps()

        if rapid == False:
            if self.stored_fast is not None and len(self.tmp_cnt) == 0:
                self.tmp_cnt.append(self.stored_fast)
                self.stored_fast = None
            self.tmp_cnt.append([x, y, z])
        elif rapid == True:
            if len(self.tmp_cnt)>0:
                self.tmp_layer.append(np.array(self.tmp_cnt))
                self.tmp_cnt = []
            self.stored_fast = [x, y, z]

        self.g.move(x,y,z,rapid=rapid,**kwargs)

        if x is not None: self.X = x
        if y is not None: self.Y = y
        if z is not None: self.Z = z

    def abs_move(self, *args, **kwargs):
        self.move(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.g, name)

    def check_tmps(self):
        "Empties the temporary layer variables by adding them to the `continuous_extrusions`"
        if len(self.tmp_cnt)>0:
            self.tmp_layer.append(np.array(self.tmp_cnt))

        if len(self.tmp_layer)>0:
            self.continuous_extrusions.append(self.tmp_layer)

        self.tmp_layer = []
        self.tmp_cnt = []

    def plot3d(self, show_all=False):
        """
        Plot the Gecode that will be printed.

        Arguments:

        show_all (bool)
            Show the extra movement lines in-between extrusion.
            Default: False
        """
        self.check_tmps()

        if show_all:
            self.g.view()
        else:
            from mpl_toolkits.mplot3d import Axes3D
            import matplotlib.pyplot as plt

            fig = plt.figure()
            ax = fig.gca(projection='3d')

            for layer in self.continuous_extrusions:
                for contour in layer:
                    X, Y, Z = contour[:, 0], contour[:, 1], contour[:, 2]
                    ax.plot(X, Y, Z, 'tab:blue')

            # Hack to keep 3D plot's aspect ratio square. See SO answer:
            # http://stackoverflow.com/questions/13685386
            max_range = np.array([self.x_max-self.x_min,
                                    self.y_max-self.y_min,
                                    self.z_max-self.z_min]).max() / 2.0

            mean_x, mean_y, mean_z = self.vertices.mean(0)
            ax.set_xlim(mean_x - max_range, mean_x + max_range)
            ax.set_ylim(mean_y - max_range, mean_y + max_range)
            ax.set_zlim(mean_z - max_range, mean_z + max_range)

            plt.show(block=True)

    def plot2d(self):
        """
        Plot a sequence of 2D slices with a slider alongside to increment the layer.
        """
        import matplotlib as mp
        import matplotlib.pyplot as plt

        self.check_tmps()

        f,ax = plt.subplots(1,2, gridspec_kw={'width_ratios': [6, 1]})
        min_lim, max_lim = min(self.x_min,self.y_min), max(self.x_max, self.y_max)
        pad = (max_lim-min_lim)/20

        def plot_layer(layer_height):
            i = int(round(layer_height/self.layer_height))
            assert i < len(self.continuous_extrusions)
            ax[0].cla()
            for contour in self.continuous_extrusions[i]:
                X, Y = contour[:, 0], contour[:, 1]
                ax[0].plot(X, Y, "tab:blue")
                ax[0].set_xlim(min_lim-pad, max_lim+pad)
                ax[0].set_ylim(min_lim-pad, max_lim+pad)

        plot_layer(0)
        sl = mp.widgets.Slider(ax[1], "Layer Height", 0, (len(self.continuous_extrusions)-1)*self.layer_height, orientation="vertical", valstep=self.layer_height, valinit=0)

        sl.on_changed(plot_layer)
        plt.show(block=True)
