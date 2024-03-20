import matplotlib.pyplot as plt
import numpy as np
import matplotlib


X7 = [2.5,2.5,2.5,2.7,2.7,2.7,2.9,2.9,2.9,3.1,3.1,3.1,3.3,3.3,3.3,3.5,3.5,3.5,3.7,3.7,3.7,3.9,3.9,3.9,4.2,4.2,4.2,4.5,4.5,4.5,4.8,4.8,4.8,5.2,5.2,5.2,5.6,5.6,5.6,6,6,6] # 'Current (mA)'
Y7 = [2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3] # 'Charge (F/mol)'
Z7 = [24,22,20,26,23,22,28,25,24,30,27,25,32,29,27,34,31,29,36,32,30,38,34,32,41,37,34,44,39,37,47,42,39,51,46,43,55,49,46,59,53,49] # 'Flow Rate (μL/min)'
C7 = [58.77069570996408, 75.81683734909782, 84.97767335297142, 74.09557354952331, 83.74146263611699, 88.09250270666192, 75.78939380350872, 84.39418537556504, 86.65099406388391, 76.05935860447373, 81.6057221153568, 86.8140332900967, 75.60241520025112, 81.82698114134314, 84.30714873904962, 76.45987532569993, 80.89794914650234, 83.61373685802732, 74.04415147987369, 80.77878173906664, 81.72680284187874, 71.49142231639796, 77.3718835436889, 79.76277381915901, 70.719577949889, 73.48573664835764, 78.16685128472449, 66.45207134360327, 70.78113369639944, 71.70642949459366, 62.58843078478421, 67.09568760357106, 70.46428817419198, 61.23626092520843, 64.07345104185053, 64.20025252300633, 55.57150632553064, 60.06823329893094, 55.60681001019623, 49.982707928864684, 49.83498526960874, 50.36308312719394] # 'Conversion (%)'

def get_productivity(product_molar_mass: float, concentration: float, conversion: float, flow_rate: float) -> float:
    """Calculates the productivity in (mg/h) from molar mass (g/mol), concentration (mol/L), conversion (%) and flow rate (μL/min)"""
    return ((product_molar_mass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60) * 1000 # Productivity in (mg/h)


def get_current_efficiency(theoretical_molar_charge: float, applied_molar_charge: float, conversion: float) -> float:
    """Calculates the current efficiency in (%) from the theoretical molar charge (F/mol), the applied molar charge (F/mol) and the conversion (%)."""
    return ((theoretical_molar_charge/applied_molar_charge) * (conversion))  # Current Efficiency in (%)


def interpret_experimental_data(product_molar_masses: list, theoretical_molar_charges: list, concentrations: list, conversions: list, flow_rates: list, applied_molar_charges: list) -> tuple[dict[str,list], dict[str,list]]:
    """Calculates the productivity (mg/h) and current efficiency (%) for a list of input values.
    
    :param product_molar_masses: List, molar mass of the product in g/mol.
    :param theoretical_molar_charges: List, stochiometric molar charge for an redox reaction in F/mol.
    :param concentrations: List, concentration of the starting material in mol/L.
    :param conversions: List, meassured conversion from educt to product in %.
    :param flow_rates: List, applied flow rates for each data point in μL/min.
    :param applied_molar_charges: List, real applied molar charges in F/mol, in contrast to the theoretical, or stochiometric molar charge.

    :raises ValueError: If input parameters are not uniform in length.
    :returns: Tuple of dictionaries with the axis label and the listed experimental values as key-value pairs. The order is: 
            (
            {'Molar Mass (g/mol)': product_molar_masses},
            {'Theoretical Molar Charge (F/mol)':theoretical_molar_charges},
            {'Concentration (mol/L)': concentrations},
            {'Conversion (%)': conversions},
            {'Flow Rate (μL/min)': flow_rates},
            {'Charge (F/mol)': applied_molar_charges},
            {'Productivity (mg/h)': productivity}, 
            {'Current Efficiency (%)': current_efficiency}
            )
    """
    length = len(concentrations)
    productivity = []
    current_efficiency = []
    if all(len(lst) == length for lst in [product_molar_masses, theoretical_molar_charges, concentrations, conversions, flow_rates, applied_molar_charges]):
        for i in range(length):
            productivity.append(get_productivity(product_molar_mass=product_molar_masses[i], concentration=concentrations[i], conversion=conversions[i], flow_rate=flow_rates[i]))
            current_efficiency.append(get_current_efficiency(theoretical_molar_charge=theoretical_molar_charges[i], applied_molar_charge=applied_molar_charges[i], conversion=conversions[i]))
        return (
            {'Molar Mass (g/mol)': product_molar_masses},
            {'Theoretical Molar Charge (F/mol)':theoretical_molar_charges},
            {'Concentration (mol/L)': concentrations},
            {'Conversion (%)': conversions},
            {'Flow Rate (μL/min)': flow_rates},
            {'Charge (F/mol)': applied_molar_charges},
            {'Productivity (mg/h)': productivity}, 
            {'Current Efficiency (%)': current_efficiency}
            )
    else:
        raise ValueError('Input list elements have to be of same length.')


def reformat_new_values(new_format_values: dict[str,list]) -> list:
    """Reformat from new data format to old data format."""
    key = list(new_format_values.keys())[0]
    old_format = new_format_values[key]
    old_format.append(key)
    return old_format







class Stem4DPlot():
    """
    Creates an 4D Stem Plot including a color gradient Bar Plot to denote the fourth dimension.

    :param x: list of values for x-axis.
    :param y: list of values for y-axis.
    :param z: list of values for z-axis.
    :param color_axis: list of values for color mark.
    :param color_code: (optional) string for restriction of plot colors. Possible values: 'red-yellow','yellow-green','green-cyan','cyan-blue','front-shift','center-shift','back-shift'

    :return: figure with 3D stem plot and color code for a fourth dimension (including a color gradient bar plot as legend).
    """

    YELLOW_PERCENTIL = 0.25
    GREEN_PERCENTIL = 0.50
    CYAN_PERCENTIL = 0.75

    def __init__(self, x: list, y: list, z: list, color_axis: list = None, *args: list, color_code: str = 'none', reverse_colors: bool = False, lower_colorscale_border = '10%', upper_colorscale_border = '10%', enumerate_datapoints: bool = False, annotation_offset: tuple = (0,0,0)) -> None:
        self.x = x[:-1]
        self.y = y[:-1]
        self.z = z[:-1]
        if color_axis != None:
            self.color_axis = color_axis[:-1]
            self.color_axis_name = color_axis[-1]#'Conversion (%)'# 'productivity (g/h)' # 'Space-Time-Yield\n(g/(F/mol)/h)' 
        else:
            self.color_axis = color_axis
            self.color_axis_name = color_axis
        self.further_color_axes = [[*args][i][:-1] for i in range(len([*args]))]
        self.x_name = x[-1]#'Flow Rate (μL/min)'
        self.y_name = y[-1]#'Charge (F/mol)'
        self.z_name = z[-1]#'Current (mA)'
        self.further_color_axes_names = [[*args][i][-1] for i in range(len([*args]))] 
        self.title_color_code = 'Color Code:'
        if color_axis != None:
            self.title_stem_plot = f'Evolution of HPLC {" ".join((self.color_axis_name.split(" ")[:-1]))}'
        else:
            self.title_stem_plot = ''
        self.valid_color_codes = ['red-yellow','cyan-blue','yellow-green','green-cyan','front-shift','center-shift','back-shift']
        self.color_code = color_code
        self.set_color_restrictions()
        self.reverse_colors = reverse_colors
        self.colors = self.get_color_gradient(self.color_axis,self.YELLOW_PERCENTIL,self.GREEN_PERCENTIL,self.CYAN_PERCENTIL,self.reverse_colors)#(0.66,0.77,0.88,reverse=False)#
        self.lower_colorscale_border, self.upper_colorscale_border = self.set_colorscale_border(lower_colorscale_border, upper_colorscale_border)
        self.enumerate_datapoints = enumerate_datapoints
        self.annotation_offset = annotation_offset
        self.get_plot()

    def set_colorscale_border(self, lower_border = None, upper_border = None):
        """
        Sets lower border of the colorscale. 
        
        :param lower_border: Either 'None' (default) => boder set to minimal value, str('xx.x%') => border set with xx.x% offset, or any specific float() value.
        :param upper_border: Either 'None' (default) => boder set to maximal value, str('xx.x%') => border set with xx.x% offset, or any specific float() value.
        :raises: ValueError if neither str() containing a number separated by a dot and '%' at the end, 'None', nor a valid float value is passed to the function.
        """
        if lower_border == None:
            lower_border_out = float(np.min(self.z))
        elif type(lower_border) == str:
            if '%' in lower_border:
                lower_border = str(lower_border).replace('%','')
                percentage = float(lower_border)
                lower_border_out = float((np.min(self.z)) - (np.min(self.z))*(percentage/100))
        elif type(lower_border) == float or type(lower_border) == int:
            lower_border_out = float(lower_border)
        else:
            raise ValueError(f'{lower_border} is an invalid value for {self.set_colorscale_border.__name__()}.')
    
        if upper_border == None:
            upper_border_out = float(np.max(self.z))
        elif type(upper_border) == str:
            if '%' in upper_border:
                upper_border = str(upper_border).replace('%','')
                percentage = float(upper_border)
                upper_border_out = float((np.max(self.z)) + (np.max(self.z))*(percentage/100))
        elif type(upper_border) == float or type(upper_border) == int:
            upper_border_out = float(upper_border)
        else:
            raise ValueError(f'{upper_border} is an invalid value for {self.set_colorscale_border.__name__()}.')

        return float(lower_border_out), float(upper_border_out)
        

    def get_color_gradient(self, color_ax: list = None, yellow_percentil: float = 0.25, green_percentil: float = 0.50, cyan_percentil: float = 0.75, reverse = False):
        """
        Takes the self.color_axis property of the class Stem4DPlot (if argument is not passed to the function) and returns a list of colors in hexadecimal notation.
        Each input element of the list is translated into a color, which represents the value within the range of values of the input list.
        Lowest to highest value: red < yellow < green < cyan < blue.
        This function takes arguments which allow to adapt the color distribution individually (default values are linearly distributed).

        :param color_ax: (optional) enables to use the method get_color_gradient() outside this class.
        :param yellow_percentil: (optional) specifies the lower percentil of the data list which is colord yellow. Default is 0.25.
        :param green_percentil: (optional) specifies the middle percentil of the data list which is colord green. Default is 0.50.
        :param yellow_percentil: (optional) specifies the upper percentil of the data list which is colord cyan. Default is 0.75.
        :param reverse: (optional) reverses the color gradient from "red<yellow<green<cyan<blue" to "red>yellow>green>cyan>blue". Default is False. 
        :return: list type object with color values in hexadecimal notation. Whereof each element of the input values is represented as a individual color tone, lowest to highest value: red < yellow < green < cyan < blue.
        """
        if self.color_axis == None:
            colors = [str(matplotlib.colors.to_hex([ 0.5, 0.5, 0.5 ])) for _ in range(len(self.x))]
            return colors
        if yellow_percentil <= green_percentil and yellow_percentil <= cyan_percentil:
            if yellow_percentil >= 0 and cyan_percentil <= 1:
                pass
            else:
                raise ValueError(f'Exception was raised from {self.__class__.__name__}, method {self.get_color_gradient.__name__}: make sure that "yellow_percentil < green_percentil < cyan_percentil" and "yellow_percentil >= 0 and cyan_percentil <= 1" holds true.')        
        else:
            raise ValueError(f'Exception was raised from {self.__class__.__name__}, method {self.get_color_gradient.__name__}: make sure that "yellow_percentil < green_percentil < cyan_percentil" and "yellow_percentil >= 0 and cyan_percentil <= 1" holds true.')
        if color_ax == None:
            color_ax = self.color_axis
        sorted_list = color_ax.copy()
        sorted_list.sort()
        colors=[]
        z_max = np.max(sorted_list)
        z_min = np.min(sorted_list)
        diff = z_max - z_min
        for i in range(len(sorted_list)):
            color_factor = color_ax[i]-z_min
            if reverse == True:
                color_factor = 1-(color_factor/diff)
            if reverse == False:
                color_factor = (color_factor/diff)
            if color_factor <= yellow_percentil and yellow_percentil != 0:
                colors.append(str(matplotlib.colors.to_hex([ 1, (color_factor/yellow_percentil), 0 ]))) # rot: (1,0,0) bis gelb: (1,1,0)
                # print(f'first r-G-b factor: {[ 1, (color_factor/yellow_percentil), 0 ]}\nred: (1,0,0) to yellow: (1,1,0)')
            elif yellow_percentil <= color_factor <= green_percentil and green_percentil != 0:
                colors.append(str(matplotlib.colors.to_hex([ 1-((color_factor-yellow_percentil)/(green_percentil-yellow_percentil)), 1, 0 ]))) # gelb: (1,1,0) bis grün: (0,1,0)
                # print(f'second R-g-b factor: {[ 1-((color_factor-yellow_percentil)/(green_percentil-yellow_percentil)), 1, 0 ]}\nyellow: (1,1,0) to green: (0,1,0)')
            elif green_percentil <= color_factor <= cyan_percentil and cyan_percentil != 0:
                colors.append(str(matplotlib.colors.to_hex([ 0 , 1, ((color_factor-green_percentil)/(cyan_percentil-green_percentil)) ]))) # grün: (0,1,0) bis cyan: (0,1,1)
                # print(f'third r-g-B factor: {[ 0 , 1, ((color_factor-green_percentil)/(cyan_percentil-green_percentil)) ]}\ngreen: (0,1,0) to cyan: (0,1,1)')
            elif color_factor >= cyan_percentil:
                colors.append(str(matplotlib.colors.to_hex([ 0 , 1-((color_factor-cyan_percentil)/(1-cyan_percentil)), 1 ]))) # cyan: (0,1,1) bis blau: (0,0,1)
                # print(f'fourth r-G-b factor: {[ 0 , 1-((color_factor-cyan_percentil)/(1-cyan_percentil)), 1 ]}\ncyan: (0,1,1) to blue: (0,0,1)')
            else:
                raise Exception(f'Exception was raised from {self.__class__.__name__}, method {self.get_color_gradient.__name__}: A missing color element was detected. Watch out for yellow percentil: {yellow_percentil}, green percentil: {green_percentil}, cyan percentil: {cyan_percentil} and this iterations color factor: {color_factor}.')
        return colors


    def set_color_restrictions(self):
        if self.color_code.lower() in self.valid_color_codes:
            if self.color_code == 'red-yellow':
                self.YELLOW_PERCENTIL = 1
                self.GREEN_PERCENTIL = 1
                self.CYAN_PERCENTIL = 1
            elif self.color_code == 'yellow-green':
                self.YELLOW_PERCENTIL = 0
                self.GREEN_PERCENTIL = 1
                self.CYAN_PERCENTIL = 1
            elif self.color_code == 'green-cyan':
                self.YELLOW_PERCENTIL = 0
                self.GREEN_PERCENTIL = 0
                self.CYAN_PERCENTIL = 1
            elif self.color_code == 'cyan-blue':
                self.YELLOW_PERCENTIL = 0
                self.GREEN_PERCENTIL = 0
                self.CYAN_PERCENTIL = 0
            elif self.color_code == 'front-shift':
                self.YELLOW_PERCENTIL = 0.40
                self.GREEN_PERCENTIL = 0.75
                self.CYAN_PERCENTIL = 0.90
            elif self.color_code == 'center-shift':
                self.YELLOW_PERCENTIL = 0.15
                self.GREEN_PERCENTIL = 0.50
                self.CYAN_PERCENTIL = 0.85
            elif self.color_code == 'back-shift':
                self.YELLOW_PERCENTIL = 0.10
                self.GREEN_PERCENTIL = 0.25
                self.CYAN_PERCENTIL = 0.60
            else:
                pass
            

    def get_plot(self):
        # self.upper_colorscale_border = (np.max(self.z)) + (np.max(self.z))*0.1 # 5 # 
        # self.lower_colorscale_border = (np.min(self.z)) - (np.min(self.z))*0.1 # 2 # 
        fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))
        for j in range(len(self.z)):
            markerline, stemline, _ = ax.stem([self.x[j]], [self.y[j]], [self.z[j]] , basefmt='none', bottom=self.lower_colorscale_border, linefmt='.') # bottom=(np.min(self.z)) # (np.min(self.z)-(np.min(self.z)*0.1))
            plt.setp(markerline,'markerfacecolor', self.colors[j], mec='k')
            plt.setp(stemline, 'color', self.colors[j], alpha=0.5)
            if self.enumerate_datapoints == True:
                ax.text(x=self.x[j]+self.annotation_offset[0],y=self.y[j]+self.annotation_offset[1],z=self.z[j]+self.annotation_offset[2], s='#'+str(j+1), color='gray')
        # Generates a non visible data point which is adjusting the maximum value at the Z-axis.
        markerline, stemline, _ = ax.stem([np.max(self.x)], [np.max(self.y)], [self.upper_colorscale_border] , basefmt='none',bottom=self.lower_colorscale_border)
        plt.setp(markerline, mec="none", mfc="none")#, zorder=3)
        plt.setp(stemline, 'color', 'none')
        # ax.text(x=self.x,y=self.y,z=self.z, s=[i+1 for i in range(len(self.z))])

        ax.set_xlabel(self.x_name)
        ax.set_ylabel(self.y_name)
        ax.set_zlabel(self.z_name)
        ax.set_title(label=self.title_stem_plot, fontdict={'fontsize': 18,
                        'fontweight' : 40,
                        'verticalalignment': 'baseline',
                        'horizontalalignment': 'center'})
        # ax.xaxis.set_label_coords(5,-5)
        # ax.yaxis.set_label_coords(5,-5)
        # ax.zaxis.set_label_coords(5,-5)
        
        gradient_resolution = 300
        if len(self.further_color_axes) > 0:
            self.further_color_axes_names.append(self.color_axis_name)
            self.further_color_axes.append(self.color_axis)
            for i in range(len(self.further_color_axes)):
                ax2 = fig.add_subplot(len(self.further_color_axes),15*len(self.further_color_axes),1+i*15*len(self.further_color_axes))
                
                print(self.further_color_axes)
                print(f'further color axes names:\n{self.further_color_axes_names}\n')
                ax2.set_xlabel(self.further_color_axes_names[i])
                ax2.xaxis.set_label_coords(1,-0.05)
                ax2.set_xticks([])
                # ax2.set_yticks([])
                ax2.set_ylim(ymin=np.min(self.color_axis),ymax=np.max(self.color_axis))
                # ax2.set_title(label=self.title_color_code, fontdict={'fontsize': 14,
                #                 'fontweight' : 40,
                #                 'verticalalignment': 'baseline',
                #                 'horizontalalignment': 'center'})
                
                # SETINGS FOR TICKS ON COLOR GRADIENT BAR
                # ax2.set_yticks([self.color_axis[i] for i in range(len(self.color_axis))]) # sets all the color-axis values as ticks.
                fragments = 5
                lst = list(np.arange(np.min(self.further_color_axes[i])+((np.max(self.further_color_axes[i])-np.min(self.further_color_axes[i]))/fragments),np.max(self.further_color_axes[i]),(np.max(self.further_color_axes[i])-np.min(self.further_color_axes[i]))/fragments))
                # lst = [round(lst[i]) for i in range(len(lst))]
                lst.append(np.max(self.further_color_axes[i]))
                lst.append(np.min(self.further_color_axes[i]))
                ax2.set_yticks(lst)
                ############################################
                print(f'index i is: {i}\n')
                if i <= len(self.valid_color_codes):
                    self.color_code = self.valid_color_codes[i]
                    self.set_color_restrictions()
                arr = np.arange(np.min(self.further_color_axes[i]),np.max(self.further_color_axes[i]),(np.max(self.further_color_axes[i])-np.min(self.further_color_axes[i]))/gradient_resolution)
                gradient_colors = self.get_color_gradient(arr.tolist(),self.YELLOW_PERCENTIL,self.GREEN_PERCENTIL,self.CYAN_PERCENTIL,self.reverse_colors)
                print(f'gradient colors are (length: {len(gradient_colors)}): {gradient_colors}')
                for j in range(gradient_resolution):
                    # print(f'further color axes, element {i},{j} is: {self.further_color_axes[i]}')
                    ax2.bar([0],[((np.max(self.further_color_axes[i]))-(((np.max(self.further_color_axes[i])-np.min(self.further_color_axes[i]))/gradient_resolution)*j))], color=gradient_colors[-1-j])
        elif self.color_axis != None:
            ax2 = fig.add_subplot(1,30,1)
            print(self.further_color_axes)
            print(f'further color axes names:\n{self.further_color_axes_names}\n')
            ax2.set_xlabel(self.color_axis_name)
            ax2.xaxis.set_label_coords(1,-0.05)
            ax2.set_xticks([])
            # ax2.set_yticks([])
            ax2.set_ylim(ymin=np.min(self.color_axis),ymax=np.max(self.color_axis))
            # ax2.set_title(label=self.title_color_code, fontdict={'fontsize': 14,
            #                 'fontweight' : 40,
            #                 'verticalalignment': 'baseline',
            #                 'horizontalalignment': 'center'})
            # SETINGS FOR TICKS ON COLOR GRADIENT BAR
            # ax2.set_yticks([self.color_axis[i] for i in range(len(self.color_axis))]) # sets all the color-axis values as ticks.
            
            fragments = 5
            lst = list(np.arange(np.min(self.color_axis)+((np.max(self.color_axis)-np.min(self.color_axis))/fragments),np.max(self.color_axis),(np.max(self.color_axis)-np.min(self.color_axis))/fragments))
            # lst = [round(lst[i]) for i in range(len(lst))]
            lst.append(np.max(self.color_axis))
            lst.append(np.min(self.color_axis))
            ax2.set_yticks(lst)
        ############################################
            arr = np.arange(np.min(self.color_axis),np.max(self.color_axis),(np.max(self.color_axis)-np.min(self.color_axis))/gradient_resolution)
            gradient_colors = self.get_color_gradient(arr.tolist(),self.YELLOW_PERCENTIL,self.GREEN_PERCENTIL,self.CYAN_PERCENTIL,self.reverse_colors)
            for k in range(gradient_resolution):
                ax2.bar([0],[((np.max(self.color_axis))-(((np.max(self.color_axis)-np.min(self.color_axis))/gradient_resolution)*k))], color=gradient_colors[-1-k])
            
        plt.show()
        



def plot_no0():
    # X = [62,62,62,62,62,62,62,124,124,124,124,124,124,124,'Flow Rate (μL/min)']
    # Y = [1,1.5,2,2.5,3,3.5,4,1,1.5,2,2.5,3,3.5,4,'Stady State Factor\n(110% reactor-residence-times)']
    # Z = [93.72112253346123, 95.84573022322742, 95.83854752269039, 96.31406281418225, 96.30871230776268, 96.65000532637242, 96.56704593728831, 46.71161255176162, 47.45527905123482, 47.81191733428544, 47.8418160397702, 47.493097883450716, 47.947730568604676, 47.858047483328434,'Conversion\n(normalized to 1)']

    X = [60,20,60,20,40,20,60,60,40,60,40,60,40,60,20,20,60,20,20,20,'Current (mA)']
    Y = [1.8,1.8,1.9,1.9,2,2,2,2.1,2.2,2.3,2.1,2.2,2.3,2.4,2.1,2.2,2.5,2.3,2.4,2.5,'Charge (F/mol)']
    Z = [207,69,196,65,124,62,187,178,113,162,118,170,108,155,59,57,149,54,52,50,'Flow Rate (μL/min)']
    C = [53.42,54.64,55.61,58.17,58.59,59.73,60.02,64.62,65.60,65.63,66.45,66.91,67.45,67.93,69.34,69.69,69.80,73.56,74.96,75.37,'Conversion (%)']

    # X = list(np.arange(1,len(X)+10))
    # Y = list(np.arange(1,len(Y)+10))
    # Z = list(np.arange(1,len(Z)+10))
    # C = list(np.arange(len(C)+10,1,-1))

        
    STY = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z)-1):
        molmass = 198.27 # g/mol
        concentration = 0.1 # mol/L
        conversion = C[i] # %
        flow_rate = Z[i] # μL/min
        charge = Y[i]
        #STY.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY.append('Productivity (mg/h)')

    
    EFF = []
    for i in range(len(Y)-1):
        molar_charge = 2
        conversion = C[i] # %
        charge = Y[i]
        EFF.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF.append('Current Efficiency (%)')
    
    Stem4DPlot(STY,EFF,C,X,color_code='none',reverse_colors=False)
    Stem4DPlot(STY,EFF,C,Y,color_code='none',reverse_colors=False)
    Stem4DPlot(STY,EFF,C,Z,color_code='none',reverse_colors=False)
    
    Stem4DPlot(X,Z,Y,C,STY,color_code='none',reverse_colors=False)
    Stem4DPlot(X,Z,Y,STY,color_code='none',reverse_colors=False)
    Stem4DPlot(X,Z,Y,EFF,color_code='none',reverse_colors=False)
    


def plot_no1():

    X1 = [010.6,015.9,021.2,011.3,016.9,022.5,'Current (mA)']
    Y1 = [3.3,3.3,3.3,3.5,3.5,3.5,'Charge (F/mol)']
    Z1 = [20,30,40,20,30,40,'Flow Rate (μL/min)']
    C1 = [86.44350384643464, 85.4320660548376, 83.1783234865462, 87.28330330129384, 84.14650323531025, 84.26567872469441, 'Conversion (%)']

    STY1 = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z1)-1):
        molmass = 198.27 # g/mol
        concentration = 0.1 # mol/L
        conversion = C1[i] # %
        flow_rate = Z1[i] # μL/min
        charge = Y1[i]
        #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY1.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY1.append('Productivity (mg/h)')

    EFF1 = []
    for i in range(len(Y1)-1):
        molar_charge = 2
        conversion = C1[i] # %
        charge = Y1[i]
        EFF1.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF1.append('Current Efficiency (%)')

    
    Stem4DPlot(X1,Z1,Y1,C1,color_code='none',reverse_colors=False)
    Stem4DPlot(X1,Z1,Y1,STY1,color_code='none',reverse_colors=False)
    Stem4DPlot(X1,Z1,Y1,EFF1,color_code='none',reverse_colors=False)



def plot_no2():

    X2 = [10,25,40,10,20,30,40,10,15,20,30,40,10,15,20,30,40,10,25,40,'Current (mA)'] # current (mA)
    Y2 = [1.9,1.9,1.9,2,2,2,2,2.1,2.1,2.1,2.1,2.1,2.2,2.2,2.2,2.2,2.2,2.3,2.3,2.3,'Charge (F/mol)'] # charges (F/mol)
    Z2 = [33,82,131,31,62,93,124,30,44,59,89,118,28,42,57,85,113,27,68,108,'Flow Rate (μL/min)'] # flow rates (μL/min)
    C2 = [92.24766448,88.60506687,86.40839247,94.69745158,92.94312015,91.44160455,90.36521374,95.34889721,94.91341883,94.18395609,92.85763473,92.01536307,95.76542419,95.42151481,94.657702,93.76309096,92.82400498,95.74959354,95.33223498,94.06059531,'Conversion (%)'] # conversion (%)

    STY2 = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z2)-1):
        molmass = 198.27 # g/mol
        concentration = 0.1 # mol/L
        conversion = C2[i] # %
        flow_rate = Z2[i] # μL/min
        charge = Y2[i]
        #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY2.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY2.append('Productivity (mg/h)')

    
    EFF2 = []
    for i in range(len(Y2)-1):
        molar_charge = 2
        conversion = C2[i] # %
        charge = Y2[i]
        EFF2.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF2.append('Current Efficiency (%)')




def plot_no3():

    
    X3 = [10,25,40,55,70,10,25,40,55,10,25,40,55,10,25,40,55,70,'Current (mA)']
    Y3 = [3.3,3.3,3.3,3.3,3.3,3.5,3.5,3.5,3.5,3.7,3.7,3.7,3.7,3.9,3.9,3.9,3.9,3.9,'Charge (F/mol)']
    Z3 = [19,47,75,104,132,18,44,71,98,17,42,67,92,16,40,64,88,112,'Flow Rate (μL/min)']
    C3 = [87.75627078791703, 77.63428550090462, 75.39589067784794, 76.32192424817816, 75.75076548202149, 92.33677567412506, 82.11702062255982, 80.72168913957472, 80.63409470142946, 79.78270546391173, 78.14047031648582, 74.98588181425046, 81.98860939724727, 93.78043057883202, 87.04474216910273, 81.79632235501023, 80.9265771892494, 81.53453351621984, 'Conversion (%)']


    STY3 = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z3)-1):
        molmass = 198.27 # g/mol
        concentration = 0.1 # mol/L
        conversion = C3[i] # %
        flow_rate = Z3[i] # μL/min
        charge = Y3[i]
        #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY3.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY3.append('Productivity (mg/h)')    

    EFF3 = []
    for i in range(len(Y3)-1):
        molar_charge = 2
        conversion = C3[i] # %
        charge = Y3[i]
        EFF3.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF3.append('Current Efficiency (%)')




    Stem4DPlot(Z3,X3,Y3,C3,color_code='none',reverse_colors=False)
    Stem4DPlot(Z3,X3,Y3,STY3,color_code='none',reverse_colors=False)
    Stem4DPlot(Z3,X3,C3,STY3,color_code='none',reverse_colors=False)





def plot_no4():

    X4 = [25,40,55,70,25,40,55,70,'Current (mA)']
    Y4 = [3.3,3.3,3.3,3.3,3.5,3.5,3.5,3.5,'Charge (F/mol)']
    Z4 = [47,75,103,131,44,71,97,124,'Flow Rate (μL/min)']
    C4 = [89.41754668181976, 85.18338397713903, 83.7327694362378, 83.13230361321713, 93.1134838197878, 86.54528948616816, 85.89241615584389, 86.57869179989818, 'Conversion (%)']


    STY4 = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z4)-1):
        molmass = 198.27 # g/mol
        concentration = 0.1 # mol/L
        conversion = C4[i] # %
        flow_rate = Z4[i] # μL/min
        charge = Y4[i]
        #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY4.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY4.append('Productivity (mg/h)')

    
    EFF4 = []
    for i in range(len(Y4)-1):
        molar_charge = 2
        conversion = C4[i] # %
        charge = Y4[i]
        EFF4.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF4.append('Current Efficiency (%)')

    Stem4DPlot(Z4,X4,Y4,C4,color_code='none',reverse_colors=False)
    Stem4DPlot(Z4,X4,Y4,STY4,color_code='none',reverse_colors=False)
    Stem4DPlot(Z4,X4,C4,STY4,color_code='none',reverse_colors=False)



def longrun_plot_third(electrode_surface_area):
    """Plot final experimental Data."""
    #####################################
    # M = [120.15] * len(X7) # molar mass g/mol
    # O = [2] * len(X7)# theoretical molar charge F/mol
    # N = [0.025] * len(X7) # concentration mol/L

    # I = X7# current
    
    # F = Y7# charge
    # R = Z7# flow rate
    # T = C7# conversion

    # P = STY7# productivity
    # E = EFF7# current efficiency
    #####################################
    I = X7 # current
    M, O, N, T, R, F, P, E = interpret_experimental_data([120.15] * len(X7), [2] * len(X7), [0.025] * len(X7), C7, Z7, Y7)
    data = [reformat_new_values(i) for i in [M, O, N, T, R, F, P, E]]
    I.append('Current (mA)')

    I_2 = [I[i]/electrode_surface_area for i in range(len(I)-1)]
    I_2.append('Current Density (mA/cm²)')
    I = I_2


    # Stem4DPlot(Z7,X7,Y7,C7)
    # Stem4DPlot(Z7,X7,Y7,STY7)
    # Stem4DPlot(Z7,X7,C7,STY7,upper_colorscale_border=None, lower_colorscale_border=None)
    # Stem4DPlot(Y7,X7,C7,STY7,upper_colorscale_border=None, lower_colorscale_border=None)
    Stem4DPlot(data[5],I,data[3],data[6],upper_colorscale_border=None, lower_colorscale_border=None)



def longrun_plot_second(electrode_surface_area):
    """Plot final experimental Data."""
    X6 = [26,26,26,30,30,30,34,34,34,38,38,38,42,42,42,46,46,46,50,50,50,54,54,54,58,58,58,62,62,62,66,66,66,70,70,70,74,74,74,78,78,78,'Current (mA)']
    Y6 = [6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,'Charge (F/mol)']
    Z6 = [26,23,20,31,26,23,35,30,26,39,33,29,43,37,32,47,40,35,51,44,38,55,47,41,60,51,45,64,55,48,68,58,51,72,62,54,76,65,57,80,69,60,'Flow Rate (μL/min)']
    C6 = [71.1233676505315, 76.14140999833413, 78.80120734140161, 71.10283965215368, 75.75090922222766, 78.66830063501952, 70.56487642180204, 74.24186393031252, 75.35848377603956, 67.30731819613428, 71.45228307578427, 73.84791689920539, 67.1457320444, 72.54373905780167, 73.98101839631845, 65.18044492890513, 67.21901708850247, 71.93896370983407, 67.40434580317938, 70.31277840065454, 70.95264374968363, 62.2770672149939, 70.54041988979725, 70.44981233143098, 67.01092365324084, 67.29014809312773, 68.31725288104742, 65.21452370675601, 66.65440877569641, 57.80975655998959, 64.21183644416956, 64.68762516299181, 62.75419407730299, 62.425625235133595, 57.00006029155876, 53.150914764469526, 62.79831980450402, 53.83281094240333, 53.72734912747963, 60.58863648287078, 52.41010851995516, 52.00552283412273, 'Conversion (%)']


    X6_2 = [X6[i]/electrode_surface_area for i in range(len(X6)-1)]
    X6_2.append('Current Density (mA/cm²)')
    X6 = X6_2

    STY6 = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z6)-1):
        molmass = 208.30 # g/mol
        concentration = 0.1 # mol/L
        conversion = C6[i] # %
        flow_rate = Z6[i] # μL/min
        charge = Y6[i]
        #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY6.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY6.append('Productivity (mg/h)')


    EFF6 = []
    for i in range(len(Y6)-1):
        molar_charge = 4
        conversion = C6[i] # %
        charge = Y6[i]
        EFF6.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF6.append('Current Efficiency (%)')

    
    # Stem4DPlot(Z6,X6,Y6,C6)
    # Stem4DPlot(Z6,X6,Y6,STY6)
    # Stem4DPlot(Z6,X6,C6,STY6,upper_colorscale_border=None, lower_colorscale_border=None)
    Stem4DPlot(Y6,X6,C6,STY6,color_code='none',reverse_colors=False,lower_colorscale_border=None,upper_colorscale_border=None)


def longrun_plot_first(electrode_surface_area):
    """Plot final experimental Data."""    
    X5 = [20,20,20,20,20,20,20,30,30,30,30,30,30,30,40,40,40,40,40,40,40,50,50,50,50,50,50,50,60,60,60,60,60,60,60,70,70,70,70,70,70,70,'Current (mA)']
    
    X5_2 = [X5[i]/electrode_surface_area for i in range(len(X5)-1)]
    X5_2.append('Current Density (mA/cm²)')
    X5 = X5_2
    
    Y5 = [3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,'Charge (F/mol)']
    Z5 = [40,38,37,36,35,34,33,60,58,56,54,53,51,50,80,77,75,73,71,69,67,100,97,94,91,88,86,84,120,116,113,109,106,103,100,140,136,131,128,124,120,117,'Flow Rate (μL/min)']
    C5 = [79.5696361531019, 81.21277271593395, 82.25677286603174, 82.20701167108939, 83.37617715444479, 82.69236098601893, 84.63965728948727, 81.64145891973794, 82.55535204246573, 82.91367866410026, 83.64315195491501, 83.50302650329826, 83.59515726196057, 84.77593786168957, 81.8452026417783, 81.98325607885921, 83.72456980388627, 83.60191612148661, 83.67226562426269, 84.87638993589354, 85.52734759759282, 82.3872763614514, 83.12816275947537, 83.7964019749412, 84.2847312028138, 84.94639793029076, 85.46043319028468, 85.75547385569526, 81.02719575328399, 82.61480391337216, 82.9469908552152, 84.01505041091897, 84.71804513279329, 85.76068101115098, 86.28322890906077, 79.3207577019601, 81.31529067619186, 82.2825085778643, 82.20449471334092, 83.26041456785352, 84.39250612700852, 84.48232543629692, 'Conversion (%)']

    STY5 = [] # space-time-yield in (g/(F/mol)/h)
    for i in range(len(Z5)-1):
        molmass = 198.27 # g/mol
        concentration = 0.1 # mol/L
        conversion = C5[i] # %
        flow_rate = Z5[i] # μL/min
        charge = Y5[i]
        #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
        STY5.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
    STY5.append('Productivity (mg/h)')

    EFF5 = []
    for i in range(len(Y5)-1):
        molar_charge = 2
        conversion = C5[i] # %
        charge = Y5[i]
        EFF5.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
    EFF5.append('Current Efficiency (%)')

    
    # Stem4DPlot(Z5,X5,Y5,color_code='none',reverse_colors=False, enumerate_datapoints=True, annotation_offset=(0,0,0))
    # Stem4DPlot(Z5,X5,Y5,C5,color_code='none',reverse_colors=False, enumerate_datapoints=True, annotation_offset=(0,0,0))
    # Stem4DPlot(Z5,X5,Y5,STY5,color_code='none',reverse_colors=False, enumerate_datapoints=True, annotation_offset=(-1,0,0))
    # Stem4DPlot(Z5,X5,C5,STY5,color_code='none',reverse_colors=False,lower_colorscale_border=None,upper_colorscale_border=None)
    Stem4DPlot(Y5,X5,C5,STY5,color_code='none',reverse_colors=False,lower_colorscale_border=None,upper_colorscale_border=None)


def main():
    # ELECTRODE_SURFACE_AREA = 56/100 # cm²

    # longrun_plot_first(ELECTRODE_SURFACE_AREA)
    # longrun_plot_second(ELECTRODE_SURFACE_AREA)
    # longrun_plot_third(ELECTRODE_SURFACE_AREA)

    # plot_no0()
    # plot_no1()
    # plot_no2()
    # plot_no3()
    # plot_no4()

    Stem4DPlot([1,2,3,4,5,6,7,8,9,'X-Axis'],[1,2,3,4,5,6,7,8,9,'Y-Axis'],[1,2,3,4,5,6,7,8,9,'Z-Axis'],[1,2,3,4,5,6,7,8,9,'Color-Axis'],color_code='none',reverse_colors=False,lower_colorscale_border=None,upper_colorscale_border=None)


if __name__ == '__main__':
    main()
    
    
