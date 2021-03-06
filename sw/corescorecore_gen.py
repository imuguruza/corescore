#!/usr/bin/python
from fusesoc.capi2.generator import Generator
import os
import shutil
import subprocess

from verilogwriter import Instance, ModulePort, Parameter, Port, VerilogWriter, Wire

HEX_TEMPLATE = '''@0000
13 00 00 00
17 05 00 00
13 05 c5 03
b7 05 00 c0
93 02 40 0b
23 80 55 00
83 02 05 00
13 05 15 00
e3 9a 02 fe
93 e2 02 10
23 90 55 00
b7 22 00 00
93 82 02 71
93 82 f2 ff
e3 9e 02 fe
6f f0 5f fc
43 6f 72 65
{} {} {} 20
73 61 79 73
20 68 65 6c
6c 6f 0a 00
'''

class CoreScoreCoreGenerator(Generator):
    def run(self):
        files = [{'corescorecore.v' : {'file_type' : 'verilogSource'}}]
        count = self.config.get('count')

        for idx in range(count):
            name = 'core_{}'.format(idx)
            memfile = name+'.hex'

            #Create hex file
            with open(memfile, 'w') as f:
                _s = '{:03}'.format(idx)
                f.write(HEX_TEMPLATE.format(hex(ord(_s[0]))[2:],
                                            hex(ord(_s[1]))[2:],
                                            hex(ord(_s[2]))[2:]))
            files.append({memfile : {'file_type' : 'user', 'copyto' : memfile }})

        self.gen_corescorecore(count)
        self.add_files(files)

    def gen_corescorecore(self, count):
        corescorecore = VerilogWriter('corescorecore')

        corescorecore.add(ModulePort('i_clk'  , 'input'))
        corescorecore.add(ModulePort('i_rst'  , 'input'))
        corescorecore.add(ModulePort('o_tdata'  , 'output', 8))
        corescorecore.add(ModulePort('o_tlast'  , 'output'))
        corescorecore.add(ModulePort('o_tvalid' , 'output'))
        corescorecore.add(ModulePort('i_tready' , 'input'))

        corescorecore.add(Wire('tdata' , count*8))
        corescorecore.add(Wire('tlast' , count))
        corescorecore.add(Wire('tvalid', count))
        corescorecore.add(Wire('tready', count))

        for idx in range(count):
            base_ports = [
                Port('i_clk', 'i_clk'),
                Port('i_rst', 'i_rst'),
                Port('o_tdata'  , 'tdata[{}:{}]'.format(idx*8+7,idx*8)),
                Port('o_tlast'  , 'tlast[{}]'.format(idx)),
                Port('o_tvalid' , 'tvalid[{}]'.format(idx)),
                Port('i_tready' , 'tready[{}]'.format(idx)),
            ]
            corescorecore.add(Instance('base', 'core_'+str(idx),
                                   [Parameter('memfile', '"core_{}.hex"'.format(idx)),
                                    Parameter('memsize', '256')],
                                   base_ports))

        arbports = [
            Port('clk', 'i_clk'),
            Port('rst', 'i_rst'),
            Port("s_axis_tdata".format(idx) , "tdata"),
            Port("s_axis_tkeep".format(idx) , "{}'d0".format(count)),
            Port("s_axis_tvalid".format(idx), 'tvalid'),
            Port("s_axis_tready".format(idx), 'tready'),
            Port("s_axis_tlast".format(idx) , 'tlast'),
            Port("s_axis_tid".format(idx)   , "{}'d0".format(count*8)),
            Port("s_axis_tdest".format(idx) , "{}'d0".format(count*8)),
            Port("s_axis_tuser".format(idx) , "{}'d0".format(count)),
            Port('m_axis_tdata ', 'o_tdata'),
            Port('m_axis_tkeep ', ''),
            Port('m_axis_tvalid', 'o_tvalid'),
            Port('m_axis_tready', 'i_tready'),
            Port('m_axis_tlast ', 'o_tlast'),
            Port('m_axis_tid   ', ''),
            Port('m_axis_tdest ', ''),
            Port('m_axis_tuser ', ''),
        ]
        arbparams = [
            Parameter('S_COUNT', count),
            Parameter('DATA_WIDTH', 8),
            Parameter('KEEP_ENABLE', 0),
            Parameter('KEEP_WIDTH', 1),
            Parameter('ID_ENABLE', 0),
            Parameter('ID_WIDTH', 8),
            Parameter('DEST_ENABLE', 0),
            Parameter('DEST_WIDTH', 8),
            Parameter('USER_ENABLE', 0),
            Parameter('USER_WIDTH', 1),
            Parameter('ARB_TYPE', '"ROUND_ROBIN"'),
            Parameter('LSB_PRIORITY', '"HIGH"'),
        ]

        corescorecore.add(Instance('axis_arb_mux', 'axis_mux', arbparams, arbports))
        corescorecore.write('corescorecore.v')

g = CoreScoreCoreGenerator()
g.run()
g.write()
