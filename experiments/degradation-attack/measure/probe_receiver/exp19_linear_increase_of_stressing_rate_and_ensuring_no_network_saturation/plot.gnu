set terminal postscript enhanced color eps font "Helvetica, 12"
set size 0.6, 0.4
set border 11
set xtics nomirror
set ytics nomirror
set style line 1 lc rgb "#85bcff" lw 5 # blue
set style line 2 lc rgb "#b5001a" lw 5 # red
set style line 3 lc rgb "#00b200" lw 7 # green
set style line 4 lc rgb "#bd4c00" lw 5 # burnt orange
set style line 5 lc rgb "#856ab0" lw 5 # purple
set style line 6 lc rgb "#b20059" lw 5 # pink
set style line 7 lc rgb "#0052b9" lw 5 # teal
set style line 8 lc rgb "#007300" lw 5 # dark-green

set output 'linear_increase_stressing_rate.eps'
set xlabel "{/:Bold Stressing Rate (Kpps)}"
set ylabel "{/:Bold Fraction of Seneitive}\n{/:Bold Connections Permitted}"
set grid
set yrange[0:1]
set ytics textcolor rgb "#b5001a"

set xtic rotate by -45
set xtics ("0" -200, "0" -100, "0" 0, "100" 100,"200" 200,"300" 300,"400" 400,"500" 500,"600" 600,"700" 700,"800" 800,"900" 900,"1000" 1000,"1100" 1100,"1200" 1200,"1300" 1300, "1400" 1400, "1500" 1500, "0" 1600, "0" 1700, "0" 1800, "0" 1900)

set y2tics nomirror
set y2label "{/:Bold Fraction of Innocuous}\n{/:Bold Packets Received}"
set y2tics textcolor rgb "#007300"
set y2range[0.999:1]

set key bottom center

plot "<(cat res_innocuous)" u 2:($3)/101000 axes x1y2 w li ls 3 ti "Egress Innocuous QUIC",\
"<(cat res_innocuous_beijing)" u 2:($3)/101000 axes x1y2 w li ls 8 ti "Ingress Innocuous QUIC",\
"<(cat res_sensitive)" u 2:3 w li ls 2 ti "Egress Sensitive QUIC",
