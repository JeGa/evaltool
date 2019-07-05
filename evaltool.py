import ipywidgets
from ipywidgets import Layout
import IPython
import pathlib
import yaml
import itertools
from matplotlib import pyplot as plt


class Plotter:
    def __init__(self):
        self.marker = None
        self.data = {}
        self.max_time = 0
        self.current_style = None

        self.num_marker = 20

        self.reset()

    def _reset_marker(self):
        self.marker = itertools.cycle(('s', 'D', '.', 'o', '^', 'v', '*', '8', 'x'))

    def _calculate_markerdistance(self, time_axis):
        max_time_new = time_axis[-1]
        if max_time_new > self.max_time:
            self.max_time = max_time_new

        marker_dist = self.max_time // self.num_marker
        step_per_point = time_axis[1]
        markevery = int(max(1.0, marker_dist // step_per_point))

        return markevery

    def legend(self, on, location=None, anchor=None):
        if not self.data:
            return

        if on:
            plt.gca().legend(loc=location, bbox_to_anchor=anchor)
        else:
            plt.gca().legend().remove()

    def save_plot(self, filename, infotext=False, fileformat='.pdf', size=None, margins=None):
        plt.figure(1)

        if size:
            plt.gcf().set_size_inches(size[0], size[1], forward=True)

        if margins:
            plt.subplots_adjust(**margins)

        if infotext:
            text_pos_y = -1

            for value in self.data.values():
                text = value[-1]

                plt.text(0, text_pos_y, text,
                         horizontalalignment='left', verticalalignment='top', transform=plt.gcf().transFigure)

                text_pos_y -= 0.6

        plt.savefig(str(filename) + fileformat, dpi=1200)

    def reset(self):
        self.style('simple')
        self.legend(on=False)
        self._reset_marker()
        self.data = {}

        plt.figure(1, clear=True)

    def add(self, data, time_axis, label, text):
        if label in self.data.keys():
            print("Label already added.")
            return

        self.data[label] = (data, time_axis, text)

        plt.figure(1)

        plt.plot(time_axis, data, label=label, markevery=self._calculate_markerdistance(time_axis),
                 linewidth=0.5, marker=next(self.marker), markerfacecolor='none')

    def style(self, plot_style, title=None, xlabel=None, ylabel=None):
        plt.figure(1)

        if plot_style == 'simple':
            plt.title('')
            plt.xlabel('')
            plt.ylabel('')

            plt.minorticks_off()
            plt.grid(False)
        elif plot_style == 'fancy':
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)

            plt.minorticks_on()
            plt.grid(which='major', linestyle='-', linewidth=0.1)
        else:
            raise ValueError("Unknown style.")

        self.current_style = plot_style


class EvalNotebook:
    def __init__(self):
        # Widgets.
        self.results_select = None
        self.data_select = None
        self.data_show = None

        self.add_btn = None
        self.clear_btn = None
        self.save_btn = None

        self.label_name = None

        self.infotext_checkbox = None
        self.simple_checkbox = None

        self.legend_dropdown = None

        # Matlab supported.
        self.legend_loc_matlab = ['best', 'upper right', 'lower left']

        # Own.
        self.legend_loc_own = ['bottom']
        self.legend_loc_none = 'no legend'

        self.title_text = None
        self.xlabel_text = None
        self.ylabel_text = None
        self.outfile_text = None

        self.main_widget = None

        # Other.
        self.inputfolder = None
        self.outputfolder = None

        self.infotext_keys = ['name', 'type', 'description', 'train_dataset', 'parameters', 'info']

        self.selected = None

        self.plot = Plotter()

        self._create_widgets()
        self._create_actions()

        self.plot.style('fancy', self.title_text.value, self.xlabel_text.value, self.ylabel_text.value)

    def _set_files(self, file_list):
        def sortfun(x):
            splitted = x.rsplit('_', maxsplit=2)
            return splitted[0], splitted[1], splitted[2][:-4]

        self.results_select.options = sorted(file_list, key=sortfun, reverse=True)

    def _create_widgets(self):
        autolayout = Layout(width='auto', height='auto')

        control_label_text = "Select file and add the result data shown on the right to the plot."
        control_label = ipywidgets.Label(
            value=control_label_text, layout=Layout(grid_area='control_label', width='auto', height='auto'))

        # Select and show.
        self.results_select = ipywidgets.Select(
            rows=20, layout=Layout(grid_area='results_select', width='auto', height='auto'))

        self.data_select = ipywidgets.Select(
            placeholder='Select file.', rows=20, layout=Layout(grid_area='data_select', width='auto', height='auto'))

        self.data_show = ipywidgets.Textarea(
            layout=Layout(grid_area='data_show', width='auto', height='99%'))

        # Buttons.
        self.add_btn = ipywidgets.Button(description='Add to plot', layout=autolayout)
        self.clear_btn = ipywidgets.Button(description='Clear', layout=autolayout)
        self.save_btn = ipywidgets.Button(description='Save', layout=autolayout)

        # Text fields.
        self.title_text = ipywidgets.Text(value='Title', description='Title', layout=autolayout)
        self.xlabel_text = ipywidgets.Text(value='xlabel', description='xlabel', layout=autolayout)
        self.ylabel_text = ipywidgets.Text(value='ylabel', description='ylabel', layout=autolayout)
        self.outfile_text = ipywidgets.Text(value='out', description='Filename', layout=autolayout)

        buttons_and_text = ipywidgets.VBox(
            [self.add_btn, self.clear_btn, self.save_btn,
             self.title_text, self.xlabel_text, self.ylabel_text, self.outfile_text],
            layout=Layout(grid_area='buttons', width='auto', height='auto'))

        # Label Text field.
        self.label_name = ipywidgets.Text(value='Label name', layout=autolayout)

        # Checkboxes.
        self.infotext_checkbox = ipywidgets.Checkbox(
            indent=False, value=True, description='Append infotext', layout=autolayout)
        self.simple_checkbox = ipywidgets.Checkbox(
            indent=False, value=False, description='Simple plot', layout=autolayout)

        # Dropdown.
        self.legend_dropdown = ipywidgets.Dropdown(
            options=self.legend_loc_matlab + self.legend_loc_own + [self.legend_loc_none],
            value=self.legend_loc_none,
            layout=autolayout)

        checkboxes_and_dropdowns = ipywidgets.VBox(
            [self.label_name, self.infotext_checkbox, self.simple_checkbox, self.legend_dropdown],
            layout=Layout(grid_area='checkboxes', width='auto'))

        # GridBox.
        self.main_widget = ipywidgets.GridBox(
            children=[control_label,
                      self.results_select, self.data_select, self.data_show,
                      buttons_and_text, checkboxes_and_dropdowns],
            layout=Layout(
                width='100%',
                grid_template_rows='auto auto auto',
                grid_template_columns='400px 120px auto',
                grid_template_areas='''
                "control_label control_label control_label"
                "results_select data_select data_show"
                "buttons checkboxes data_show"
                ''',
                border='solid'))

    def _infotext(self):
        return yaml.dump({key: self.selected[key] for key in self.infotext_keys})

    def _create_actions(self):
        def add_btn_click(_):
            if self.selected:
                file_name = self.results_select.value.rsplit('.', maxsplit=1)[0]
                data_name = self.data_select.value

                if data_name is not None:
                    data = self.selected['loss'][data_name][0]
                    time_axis = self.selected['loss'][data_name][1]

                    text = self._infotext()

                    # Determine label name.
                    if self.label_name.value and self.label_name.value != 'Label name':
                        label_name = self.label_name.value
                    else:
                        label_name = file_name + '_' + data_name

                    self.plot.add(data, time_axis, label_name, text)

        def clear_btn_click(_):
            self.plot.reset()
            self.simple_checkbox.value = True

        def save_btn_click(_):
            self.plot.save_plot(self.outputfolder / self.outfile_text.value, self.infotext_checkbox.value)

        self.add_btn.on_click(add_btn_click)
        self.clear_btn.on_click(clear_btn_click)
        self.save_btn.on_click(save_btn_click)

        def simple_checkbox_toggle(_):
            if self.simple_checkbox.value:
                self.plot.style('simple')
            else:
                self.plot.style('fancy', self.title_text.value, self.xlabel_text.value, self.ylabel_text.value)

        self.simple_checkbox.observe(simple_checkbox_toggle, names='value')

        def legend_dropdown_toggle(_):
            value = self.legend_dropdown.value

            if value == self.legend_loc_none:
                self.plot.legend(on=False)
            elif value in self.legend_loc_matlab:
                self.plot.legend(on=True, location=value)
            elif value in self.legend_loc_own:
                if value == 'bottom':
                    self.plot.legend(on=True, location='upper center', anchor=(0.5, -0.13))

        self.legend_dropdown.observe(legend_dropdown_toggle, names='value')

        def results_select_observe(x):
            selected = x['new']

            # Display in data select view.
            filepath = self.inputfolder / selected

            try:
                with filepath.open('r') as f:
                    yaml_data = yaml.safe_load(f)

                losses = list(yaml_data['loss'].keys())
                if not losses:
                    raise ValueError("No loss data in file.")

                self.data_select.options = losses

                self.selected = yaml_data

                self.data_show.value = self._infotext()
            except Exception as e:
                print(e)
                self.selection_valid = None

        self.results_select.observe(results_select_observe, names='value')

    def run(self, inputfolder, outputfolder):
        self.inputfolder = pathlib.Path(inputfolder)
        self.outputfolder = pathlib.Path(outputfolder)

        self._set_files([p.name for p in self.inputfolder.glob('*.yml')])

        IPython.display.display(self.main_widget)
