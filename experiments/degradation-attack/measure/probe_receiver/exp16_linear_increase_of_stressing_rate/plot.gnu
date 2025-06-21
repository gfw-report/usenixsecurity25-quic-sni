set terminal postscript enhanced color eps font "Helvetica, 12"
set size 0.6, 0.4
set border 3
set xtics nomirror
set ytics nomirror
set style line 1 lc rgb "#85bcff" lw 5 # blue
set style line 2 lc rgb "#b5001a" lw 5 # red
set style line 3 lc rgb "#00b200" lw 5 # green
set style line 4 lc rgb "#bd4c00" lw 5 # burnt orange
set style line 5 lc rgb "#856ab0" lw 5 # purple
set style line 6 lc rgb "#b20059" lw 5 # pink
set style line 7 lc rgb "#0052b9" lw 5 # teal

set output 'linear_increase_stressing_rate.eps'
set xlabel "{/:Bold Stressing Rate (Kpps)}"
set ylabel "{/:Bold Fraction Permitted}"
set grid
set yrange[0:1]
set xtic rotate by -45
set xtics ("100" 100,"200" 200,"300" 300,"400" 400,"500" 500,"600" 600,"700" 700,"800" 800,"900" 900,"1000" 1000,"1100" 1100,"1200" 1200,"0" 1300,"0" 1400, "0" 1500, "0" 1600)

plot "<(cat res)" u 2:3 w li ls 2 ti "Sensitive QUIC Traffic"
