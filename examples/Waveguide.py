import BPG
from bag.layout.util import BBox


class SingleModeWaveguide(BPG.PhotonicTemplateBase):
    def __init__(self, temp_db,
                 lib_name,
                 params,
                 used_names,
                 **kwargs,
                 ):
        """ Class for generating a single mode waveguide shape in Lumerical """
        BPG.PhotonicTemplateBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
        self.params = params

    @classmethod
    def get_params_info(cls):
        return dict(
            width='Waveguide width in microns',
            length='Waveguide length in microns'
        )

    @classmethod
    def get_default_param_values(cls):
        return dict(
            width=.6,
            length=10
        )

    def draw_layout(self):
        """ Specifies the creation of the lumerical shapes """
        # Pull in parameters from dictionary for easy access
        width = self.params['width']
        length = self.params['length']

        # Add waveguide
        self.add_rect(layer='SI',
                      bbox=BBox(left=-.5 * width,
                                bottom=-.5 * length,
                                right=0.5 * width,
                                top=.5 * length,
                                resolution=self.grid.resolution,
                                unit_mode=False)
                      )

        self.add_photonic_port(name='FDEPort',
                               center=(0, 0),
                               orient='R90',
                               width=width,
                               layer='SI')


def test_wg():
    spec_file = 'BPG/examples/specs/WaveguideTB.yaml'
    plm = BPG.PhotonicLayoutManager(spec_file)
    plm.generate_template()
    plm.generate_content()
    plm.generate_gds()
    plm.generate_flat_content()
    plm.generate_flat_gds()
    plm.generate_lsf()


if __name__ == '__main__':
    """ Unit Test for the waveguide class """
    test_wg()
