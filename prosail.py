import numpy
from avoplot import plugins, series, controls
import avoplot
import pyprosail
from avoplot.gui import widgets
import wx
import wx.lib.agw.floatspin as FS

plugin_is_GPL_compatible = True

class ProSAILSeries(series.XYDataSeries):
    """
    Define our own data series type for Sine data. Unlike for subplots, when 
    defining custom data series, we do override the __init__ method.
    """
    def __init__(self, *args, **kwargs):
        super(ProSAILSeries, self).__init__(*args, **kwargs)
        
        #add a control for this data series to allow the user to change the 
        #frequency of the wave using a slider.
        self.add_control_panel(ProSAILControl(self))
    
    
    @staticmethod
    def get_supported_subplot_type():
        """
        This is how we restrict which data series can be plotted into which 
        types of subplots. Specialised subplots may provide controls for dealing
        with very specific types of data - for example, our TrigFuncSubplot 
        allows the x-axis to be switched between degrees and radians, it would
        therefore make no sense to allow time series data to be plotted into it.
        However, it might make sense to allow a SineWaveSeries to be plotted 
        into a general AvoPlotXYSuplot, and therefore this is permitted by 
        AvoPlot. The rule is as follows:
        
          A data series may be plotted into a subplot if the subplot is an
          instance of the class returned by its get_supported_subplot_type()
          method or any of its base classes.
        """
        return avoplot.subplots.AvoPlotXYSubplot

class ProSAILControl(controls.AvoPlotControlPanelBase):
    """
    Control panel for sine wave data series allowing their frequency to 
    be changed using a slider.
    """
    def __init__(self, series):
        #call the parent class's __init__ method, passing it the name that we
        #want to appear on the control panels tab.
        super(ProSAILControl, self).__init__("ProSAIL Parameters")
        
        #store the data series object that this control panel is associated with, 
        #so that we can access it later
        self.series = series
    
    def add_slider(self, name, caption, defaultval, minval, maxval, inc, handler):
        #create a label for the slider
        label = wx.StaticText(self, wx.ID_ANY, caption)
        self.Add(label, 0,
                 wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_HORIZONTAL,
                 border=10)

        #create a frequency slider
        #self.slider = wx.Slider(self, wx.ID_ANY, value=0.01, minValue=0.01,
        #                        maxValue=2.0, style=wx.SL_LABELS)
        slider_ref = FS.FloatSpin(self, -1, min_val=minval, max_val=maxval,
                                 increment=inc, value=defaultval)
        slider_ref.SetFormat("%f")
        slider_ref.SetDigits(2)

        self.sliders[name] = slider_ref
        
        #add the slider to the control panel's sizer
        self.Add(self.sliders[name], 0, 
                 wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, border=0)
        
        #register an event handler for slider change events
        FS.EVT_FLOATSPIN(self, self.sliders[name].GetId(), 
                                      handler)


    def setup(self, parent):
        """
        This is where all the controls get added to the control panel. You 
        *must* call the setup method of the parent class before doing any of
        your own setup.
        """
        
        #call parent class's setup method - do this before anything else
        super(ProSAILControl, self).setup(parent)

        self.sliders = {}
        self.add_slider('EWT', "Equivalent Water Thickness (cm)", 0.1, 0, 1, 0.01, self.update_plot)
        self.add_slider('Chloro', "Chlorophyll content (ug per cm^2)", 40, 0, 100, 1, self.update_plot)
        self.add_slider('Carot', "Carotenoid content (ug per cm^2)", 8, 0, 100, 1, self.update_plot)
        self.add_slider('N', "Structure Coefficient", 1.5, 0, 3, 0.1, self.update_plot)

    
    
    def update_plot(self, evnt):
        """
        Event handler for frequency slider change events.
        """
        ewt = self.sliders['EWT'].GetValue()
        chloro = self.sliders['Chloro'].GetValue()
        carot = self.sliders['Carot'].GetValue()
        N = self.sliders['N'].GetValue()


        res = pyprosail.run(N, chloro, carot, 0, ewt, 0.009, 1, 3, 0.01, 30, 0, 10, 0, pyprosail.Planophile)
        
        #change the data in the series object
        self.series.set_xy_data(xdata=res[:,0], ydata=res[:,1])
        
        #draw our changes on the display
        self.series.update()

class ProsailPlugin(plugins.AvoPlotPluginSimple):
        def __init__(self):
            super(ProsailPlugin, self).__init__("PyProSAIL",
                                                ProSAILSeries)

            self.set_menu_entry(['Optical RS','PyProSAIL'],
                                "Plot outputs from the PyProSAIL vegetation reflectance model")


        def plot_into_subplot(self, subplot):


            res = pyprosail.run(1.5, 40, 8, 0, 0.1, 0.009, 1, 3, 0.01, 30, 0, 10, 0, pyprosail.Planophile)

            data_series = ProSAILSeries("ProSAIL Output", xdata=res[:,0],
                                              ydata=res[:,1])

            subplot.add_data_series(data_series)

            return True


plugins.register(ProsailPlugin())