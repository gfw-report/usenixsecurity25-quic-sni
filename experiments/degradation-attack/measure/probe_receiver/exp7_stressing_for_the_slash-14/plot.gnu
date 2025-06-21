#!/usr/local/bin/gnuplot --persist

set terminal postscript enhanced color eps font "Helvetica, 20"
set size 1, 0.7
set border 3
set xtics nomirror
set ytics nomirror

set output "quic-rand-exp.eps"
set ylabel "{/ Helvetica-Bold Fraction Permitted}"
#set xlabel "{/ Helvetica-Bold Date and Time (CST)}"
set xlabel "{/ Helvetica-Bold Hour of the Day}"

set ylabel font "Helvetica-Bold, 24"
set xlabel font "Helvetica-Bold, 24"
set grid
set xdata time
set timefmt "%Y-%m-%d_%H:%M:%S"
#set format x "%m/%d %H:%M"
set datafile missing
#set xtics rotate by 55 right
set yrange [0:1]
#set xrange ["2025-01-01_05:20:00":]
set xrange ["2025-01-04_08:00:00":"2025-01-05_13:00:00"]
#unset xtics
set format x "%H"
set key center right
#set key outside top

plot "<(cat res_stress_quic)" u 1:2 w lines ti "During QUIC-stressing" lw 5,\
"<(cat res_no-stress)" u 1:2 w lines ti "During no stressing" lw 5,\
"<(cat res_stress_rand)" u 1:2 w lines ti "During Random-stressing" lw 5,\
