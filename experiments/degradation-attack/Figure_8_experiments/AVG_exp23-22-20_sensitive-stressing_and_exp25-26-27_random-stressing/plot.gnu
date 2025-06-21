set termoption dash

set terminal postscript enhanced color eps font "Helvetica, 18"
set size 1, 0.7
set border 11
set xtics nomirror
set ytics nomirror
set style line 1 lc rgb "#85bcff" lw 5 # blue
set style line 2 lc rgb "#b5001a" lw 5 # red
set style line 3 lc rgb "#00b200" lw 5 # green
set style line 4 lc rgb "#bd4c00" lw 5 # burnt orange
set style line 5 lc rgb "#856ab0" lw 5 # purple
set style line 6 lc rgb "#b20059" lw 5 # pink
set style line 7 lc rgb "#0052b9" lw 5 # teal
set style line 8 lc rgb "#007300" lw 5 # dark-green
set style line 9 lc rgb "#e86f81" lw 5 # light-red

set output 'stressing_rates.eps'
set xlabel "{/:Bold Stressing Rate (Kpps)}"
set ylabel "{/:Bold Fraction of Censored}\n{/:Bold Connections Permitted}"
set ylabel textcolor rgbcolor "#b5001a"
set grid
set yrange[0:1]
set ytics textcolor rgb "#b5001a"

set xtic rotate by -45
set xtics ("0" -200, "0" -100, "0" 0, "100" 100,"200" 200,"300" 300,"400" 400,"500" 500,"600" 600,"700" 700,"800" 800,"900" 900,"1000" 1000,"1100" 1100,"1200" 1200,"1300" 1300, "1400" 1400, "1500" 1500, "0" 1600, "0" 1700, "0" 1800, "0" 1900)

set y2tics nomirror
set y2label "{/:Bold Fraction of Control}\n{/:Bold Packets Received}"
set y2label textcolor rgbcolor "#007300"
set y2tics textcolor rgb "#007300"
set y2range[0.99:1]

set key above center vertical maxrows 2 font ",14"
#set key above center font ",14"

plot "<(cat res_innocuous)" u 1:($2)/101000 axes x1y2 w lp ls 3 pt 4 ti "Egress Control Traffic",\
"<(cat res_innocuous_beijing)" u 1:($2)/101000 axes x1y2 w lp ls 8 pt 2 ti "Ingress Control Traffic",\
"<(cat res_sensitive)" u 1:2 w li ls 2 ti "Censored Traffic (Censored Stressing)",\
"<(cat res_sensitive_random_stressing)" u 1:2 w li ls 9 ti "Censored Traffic (Random Stressing)"
