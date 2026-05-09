# Timing constraints — ASAP7 7nm, 1 GHz target clock
create_clock -name clk -period 1.0 [get_ports clk]

set_input_delay  -clock clk -max 0.2 [all_inputs]
set_output_delay -clock clk -max 0.2 [all_outputs]

# ALU combinational paths
set_max_delay 0.8 -combinational -from [get_ports {ui_in[*] uio_in[*]}] \
                                 -to   [get_ports {uo_out[*]}]

set_false_path -from [get_ports rst_n]
